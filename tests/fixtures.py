import moto
import boto3
import pytest


@pytest.fixture
def data_table():
    """
    Create a mock DynamoDB table for testing using moto.
    :return: The mock table.
    """
    with moto.mock_aws():
        client = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "uuid", "AttributeType": "S"},
            ],
            TableName="mock_table",
            KeySchema=[
                {"AttributeName": "uuid", "KeyType": "HASH"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        yield "mock_table"


@pytest.fixture
def data_table_with_data(data_table):
    """
    Adds data to the mock dynamodb table.
    :param data_table: Moto mock table.
    :return: Mock table with data.
    """
    # create the table using the moto mock table.
    table = boto3.resource("dynamodb").Table(data_table)

    # create the mock data set.
    data_set = [
        {"uuid": "abcd-1234", "classification": "class1", "title": 'title1', "description": "desc1"},
        {"uuid": "abcd-5678", "classification": "class2", "title": 'title2', "description": "desc2"}
    ]

    # add the data to the mock table.
    for data in data_set:
        table.put_item(Item=data)

    yield table
