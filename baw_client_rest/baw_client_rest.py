"""Contains a simple client for BAW REST Endpoints"""

import time
from botocore.exceptions import ClientError
import boto3
import requests
from requests import RequestException


class Client:  # pylint: disable=too-few-public-methods
    """
    Class to simplify connecting to the REST endpoints of BAW,
    Manages retrieving and caching CSRF tokens,
    and provides a simple method for sending messages to BAW: send_request

    To instantiate provide a BAW username and Password, the rest endpoint,
    the endpoint from which your csrf token will be retrieved,
    the name of a dynamo db table for csrf caching and a logger.

    All logs will be sent to the provided logger
    """

    CSRF_CACHE = {"csrf_token": None, "expiration": None}

    def __init__(
        self, username, password, logger, url=None, csrf_url=None, cache=None
    ):  # pylint: disable=too-many-arguments
        self.username = username
        self.password = password
        self.url = endpoint
        self.baw_csrf_url = csrf_endpoint
        self.csrf_cache = cache_name
        self.logger = logger

        self.url = url
        if url is None:
            self.url = self._getenv("BAW_ENDPOINT")

        self.baw_csrf_url = csrf_url
        if csrf_url is None:
            self.baw_csrf_url = self._getenv("BAW_CSRF_URL")
        self._setup_dynamo_cache(cache, logger)

    def _setup_dynamo_cache(self, cache, logger):
        if cache is None:
            csrf_cache = getenv("CSRF_CACHE")
            if csrf_cache is None:
                logger.info(
                    "No cache name provided, dynamo db csrf caching is disabled"
                )
            else:
                self.dynamo_client = boto3.client("dynamodb")
        self.dynamo_cache = csrf_cache

    def send_request(self, message):
        """Send a JSON object to the provided BAW endpoint"""
        csrf_token = self._check_token()
        task_resp = requests.post(
            url=self.url,
            headers={"BPMCSRFToken": csrf_token},
            auth=(self.username, self.password),
            json=message,
        )
        if task_resp.status_code != 201:
            raise ConnectionError(
                f"Failed to send message to BAW with status code: {task_resp.status_code},"
                "and response: {task_resp.text}"
            )

    def _check_token(self):
        """Implements TTL-based local, remote DynamoDB and fallback caching
        for BAW (BPM) CSRF tokens"""
        now = int(time.time())

        # Check for csrf token cached as class attribute
        csrf_cache = Client.CSRF_CACHE
        if csrf_cache["csrf_token"] is not None:
            if csrf_cache["expiration"] > now:
                self.logger.debug("Retrieved CSRF token from global variable")
                return csrf_cache["csrf_token"]

        # Check for csrf token cahed in dynamo DB
        if self.dynamo_cache is not None:
            csrf_cache = self._get_csrf_from_dynamo(now)
            if csrf_cache is not None:
                if csrf_cache["expiration"] > now:
                    self.logger.debug("Retrieved CSRF token from dynamodb")
                    Client.CSRF_CACHE = csrf_cache
                    return csrf_cache["csrf_token"]

        # Retrieve a new CSRF token from BAW
        try:
            csrf_resp = requests.post(
                self.baw_csrf_url,
                auth=(self.username, self.password),
                json={"requested_lifetime": 7200},
            )
        except (ConnectionError, RequestException) as error:
            raise ConnectionError("Cannot get CSRF token") from error
        if csrf_resp.status_code != 201:
            if csrf_resp.status_code == 200:
                self.logger.error(
                    "Cannot get CSRF token: redirected to login page by BAW"
                )
                self.logger.debug("BAW response: %s", csrf_resp.text)
            else:
                raise ConnectionError(
                    "Cannot get CSRF token: request failed with status code {csrf_resp.status_code}"
                )
        csrf_cache = csrf_resp.json()
        # Subtracting 30 seconds to allow for bad clocks and latency
        csrf_cache["expiration"] = (csrf_cache["expiration"] - 30) + now
        self.logger.debug("Received new CSRF token from BAW")
        Client.CSRF_CACHE = csrf_cache

        # Cache csrf token in dynamo DB
        if self.dynamo_cache is not None:
            self.save_csrf_to_dynamo(csrf_cache)

        return csrf_cache["csrf_token"]

    def _get_csrf_from_dynamo(self, now):
        try:
            response = self.dynamo_client.get_item(
                TableName=self.dynamo_cache,
                Key={"user": {"S": self.username}},
                ProjectionExpression="csrf_token, expires",
            )
            if response and response.get("Item"):
                csrf_cache = {
                    "expiration": int(response["Item"]["expires"]["N"]),
                    "csrf_token": response["Item"]["csrf_token"]["S"],
                }
                return csrf_cache
            return None
        except (ClientError, KeyError) as error:
            self.logger.error("Failed to access dynamodb cache", exc_info=error)

    def _save_csrf_to_dynamo(self, csrf_cache):
        try:
            response = self.dynamo_client.put_item(
                TableName=self.csrf_cache,
                Item={
                    "user": {"S": self.username},
                    "expires": {"N": str(csrf_cache["expiration"])},
                    "csrf_token": {"S": csrf_cache["csrf_token"]},
                },
            )
            self.logger.debug("Stored new CSRF token in dynamodb cache")

        except ClientError as error:
            self.logger.error("Failed to cache CSRF token in dynamodb", exc_info=error)
