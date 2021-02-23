import os
import pytest
from moto import mock_dynamodb2
import requests_mock
import boto3


@pytest.fixture
def working_setup():

    # BAW credentials
    os.environ["BAW_ENDPOINT"] = "https://example.com/endpoint"
    os.environ["BAW_CSRF_URL"] = "https://example.com/csrf"

    # AWS settings
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"
    os.environ["CSRF_CACHE"] = "bpm-csrf-cache-unit-testing"

    with mock_dynamodb2():
        conn = boto3.client("dynamodb")
        conn.create_table(
            AttributeDefinitions=[{"AttributeName": "user", "AttributeType": "S"}],
            TableName="bpm-csrf-cache-unit-testing",
            KeySchema=[
                {"AttributeName": "user", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        conn.update_time_to_live(
            TableName="bpm-csrf-cache-unit-testing",
            TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires"},
        )
        with requests_mock.Mocker() as rmock:
            rmock.post(
                os.getenv("BAW_CSRF_URL"),
                [
                    {
                        "json": {"expiration": 7200, "csrf_token": "test_token_1"},
                        "status_code": 201,
                    },
                    {
                        "json": {"expiration": 7200, "csrf_token": "test_token_2"},
                        "status_code": 201,
                    },
                ],
            )
            rmock.post(
                os.getenv("BAW_ENDPOINT"),
                [{"json": {"body": "response_from_baw_1"}, "status_code": 201}],
            )
            yield rmock