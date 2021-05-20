# baw-client-rest
Python client for making REST requests to BAW from aws lambdas.

requires a dynamo db table to cache the csrf token retrieved from BAW.

# Installation
The package can be installed using
`pip install -e git+https://github.com/ONSdigital/baw-client-rest/@{version}#egg=baw-client-rest`

where {version} is a tagged version on the repo, e.g. `v0.2`

# Usage
To use this client:

## Importing:
```python
from baw_client_rest.baw_client_rest import Client
```

## Instantiating:
Instantiating the client requires the following arguments:

**Username**: *string* - the BAW username you intend to connect with.

**Password**: *string* - the BAW password you intend to connect with.

**url**: *string* - the BAW endpoint you wish to connect to.

**baw_csrf_url**: *string* - the url that provides your baw CSRF tokens.

**csrf_cache**: *string* - the name of the Dynamo db table where you will cache your csrf token.

**logger**: *python logger or child class instance* - the logger that you wish to direct logs to.

# Sending a message
to send a message to BAW use:
`client_instance.send_request(message)`
where client_instance is an instance of the Client class, and message is the message object which you wish to send (this will be converted to a json string)

# CSRF table setup
This client requires a
 dynamo db table, to cache the csrf token from BAW. This can be set up as follows using terraform: (where your-resource-name is the name you wish to use for your csrf cache table)
```
resource "aws_dynamodb_table" "csrf_table" {
  name         = "your-resource-name"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user"
  attribute {
    name = "user"
    type = "S"
  }
  ttl {
    attribute_name = "expires"
    enabled        = true
  }
}
```
You will also need to add appropriate permissions to this table in your lambda.