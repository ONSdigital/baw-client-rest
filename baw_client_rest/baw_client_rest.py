"""Contains a simple client for BAW REST Endpoints"""

import time
from os import getenv
from botocore.exceptions import ClientError
import boto3
import requests
from requests import RequestException


class Client:
    """
    Class to simplify connecting to the REST endpoints of BAW,
    Manages retrieving and caching CSRF tokens,
    and provides a simple method for sending messages to BAW: send_request

    To instantiate provide a BAW username and Password, the rest endpoint,
    the endpoint from which your csrf token will be retrieved,
    the name of a dynamo db table for csrf caching and a logger.

    All logs will be sent to the provided logger
    """

    CSRF_CACHE = None

    def __init__(self, username, password, endpoint, csrf_endpoint, cache_name, logger):
        self.username = username
        self.password = password
        self.url = endpoint
        self.baw_csrf_url = csrf_endpoint
        self.csrf_cache = cache_name
        self.logger = logger

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

        # Check for csrf token cached as class attribute
        now = int(time.time())
        csrf_cache = Client.CSRF_CACHE
        if csrf_cache is not None:
            if csrf_cache["expiration"] > now:
                self.logger.debug("Retrieved CSRF token from global variable")
                return csrf_cache["csrf_token"]

        # Check for csrf token cahed in dynamo DB
        try:
            client = boto3.client("dynamodb")
            response = client.get_item(
                TableName=self.csrf_cache,
                Key={"user": {"S": self.username}},
                ProjectionExpression="csrf_token, expires",
            )
            if response and response.get("Item"):
                csrf_cache = {
                    "expiration": int(response["Item"]["expires"]["N"]),
                    "csrf_token": response["Item"]["csrf_token"]["S"],
                }
                if csrf_cache["expiration"] > now:
                    self.logger.debug("Retrieved CSRF token from DynamoDB cache")
                    Client.CSRF_CACHE = csrf_cache
                    return csrf_cache["csrf_token"]
        except (ClientError, KeyError) as error:
            self.logger.error("Failed to access dynamodb cache", exc_info=error)

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
        self.logger.debug("Recieved new CSRF token from BAW")
        Client.CSRF_CACHE = csrf_cache

        # Cache csrf token in dynamo DB
        try:
            response = client.put_item(
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

        return csrf_cache["csrf_token"]
