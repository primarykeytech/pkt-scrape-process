import moto
import boto3
import boto3.dynamodb.conditions as conditions
import pytest


@pytest.fixture
def data_table():
    with moto.mock_aws():
        client = boto3.client("dynamodb")
        client.create_table(
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"}
            ],
            TableName="my_table",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )

        yield "my_table"


@pytest.fixture
def data_table_with_transactions(data_table):
    """Creates transactions for a client with a total of 9"""

    table = boto3.resource("dynamodb").Table(data_table)

    txs = [
        {"PK": "CLIENT#123", "SK": "TX#a", "total": 3},
        {"PK": "CLIENT#123", "SK": "TX#b", "total": 3},
        {"PK": "CLIENT#123", "SK": "TX#c", "total": 3},
    ]

    for tx in txs:
        table.put_item(Item=tx)


def test_with_tx_client(data_table_with_transactions):
    """
    Tests the lambda function for a client that has some transactions.
    Their total value is 9.
    """

    dynamodb_resource = boto3.resource("dynamodb")
    table = dynamodb_resource.Table("my_table")

    # Get all items in the partition that start with TX#
    response = table.query(
        KeyConditionExpression= \
            conditions.Key("PK").eq(f"CLIENT#123") \
            & conditions.Key("SK").eq(f"TX#c")
    )

    response_items = response["Items"]
    item_total = response_items[0]["total"]
    print(response_items)
    print(response_items[0]["total"])

    expected_total = 3

    assert item_total == expected_total
