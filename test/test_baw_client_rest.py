import os
import logging
from baw_client_rest.baw_client_rest import Client
import boto3


def test_happy_path(working_setup):
    # CSRF token is retrieved and a message sent to the endpoint
    logger = logging.getLogger()
    client = Client("user", "pw", logger)
    client.send_request({"body": "message_to_baw"})
    assert working_setup.request_history[0].url == os.getenv("BAW_CSRF_URL")
    assert working_setup.request_history[0].json() == {"requested_lifetime": 7200}

    assert working_setup.request_history[1].url == os.getenv("BAW_ENDPOINT")
    assert working_setup.request_history[1].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[1].json() == {"body": "message_to_baw"}


def test_local_caching(working_setup, caplog):
    # delete the dynamo table so that only local caching is active
    conn = boto3.client("dynamodb")
    conn.delete_table(TableName="bpm-csrf-cache-unit-testing")
    Client.CSRF_CACHE = None

    # making an initial call
    logger = logging.getLogger()
    client = Client("user", "pw", logger)
    client.send_request({"body": "message_to_baw"})
    assert working_setup.request_history[0].url == os.getenv("BAW_CSRF_URL")
    assert working_setup.request_history[0].json() == {"requested_lifetime": 7200}
    assert working_setup.request_history[1].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[1].json() == {"body": "message_to_baw"}

    # Same CSRF token is re-used
    client.send_request({"body": "message_to_baw_2"})
    assert working_setup.request_history[2].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[2].json() == {"body": "message_to_baw_2"}

    # Same CSRF token is re-used even if class is re-instantiated
    client = Client("user", "pw", logger)
    client.send_request({"body": "message_to_baw_3"})
    assert working_setup.request_history[3].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[3].json() == {"body": "message_to_baw_3"}

    Client.CSRF_CACHE = None
    # New csrf token retrieved if cache is destroyed
    client.send_request({"body": "message_to_baw_4"})
    assert working_setup.request_history[5].headers["BPMCSRFToken"] == "test_token_2"
    assert working_setup.request_history[5].json() == {"body": "message_to_baw_4"}
    errors = [
        record.message for record in caplog.records if record.levelname == "ERROR"
    ]
    # Check that the broken dynamodb table has been noted in the logs
    assert "Failed to access dynamodb cache" in errors
    assert "Failed to cache CSRF token in dynamodb" in errors


def test_dynamo_caching(working_setup):
    logger = logging.getLogger()
    Client.CSRF_CACHE = None
    client = Client("user", "pw", logger)
    client.send_request({"body": "message_to_baw"})
    assert working_setup.request_history[1].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[1].json() == {"body": "message_to_baw"}

    # Uses cached csrf token even if local cache is cleared
    Client.CSRF_CACHE = None
    client.send_request({"body": "message_to_baw_2"})
    assert working_setup.request_history[2].headers["BPMCSRFToken"] == "test_token_1"
    assert working_setup.request_history[2].json() == {"body": "message_to_baw_2"}
