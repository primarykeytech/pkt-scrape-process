import pytest
from pktscrape.module_db import DynamoDb
from pktscrape.module_scraping import Experience
from fixtures import data_table, data_table_with_data


def test_create_record(data_table, data_table_with_data):
    """
    Test the create_record function.
    :param data_table: mock table.
    :param data_table_with_data: mock table with data.
    """
    # create an object and set the values.
    obj_exp = Experience()
    obj_exp.uuid = "00000000-1111-2222-3333-44444444444444"
    obj_exp.title = "John Smith Experience"
    obj_exp.classification = "aspirin"
    obj_exp.description = "This is a test description"

    # using db object.
    obj_db = DynamoDb()

    # overwrite the table with the mock table.
    obj_db.table = data_table_with_data

    # create the record in the mock table.
    obj_db.create_record(obj_exp)

    # get the record from the mock table.
    obj_item = obj_db.read_one_by_id(obj_exp.uuid)

    # run the test to see if the record was created with the object above.
    assert obj_item.classification == "aspirin"


def test_create_multiple_records(data_table, data_table_with_data):
    """
    Test the create_multiple_records function.
    :param data_table: mock table.
    :param data_table_with_data: mock table with data.
    """
    # create an object and set the values.
    obj_exp1 = Experience()
    obj_exp1.uuid = "11111111-1111-2222-3333-44444444444444"
    obj_exp1.title = "Jane Smith Experience"
    obj_exp1.classification = "aspirin"
    obj_exp1.description = "This is a test description"

    # create an object and set the values.
    obj_exp2 = Experience()
    obj_exp2.uuid = "22222222-1111-2222-3333-44444444444444"
    obj_exp2.title = "Baby Smith Experience"
    obj_exp2.classification = "aspirin"
    obj_exp2.description = "This is a test description"

    # list to hold the objects.
    list_obj_exp = [obj_exp1, obj_exp2]

    # using db object.
    obj_db = DynamoDb()

    # overwrite the table with the mock table.
    obj_db.table = data_table_with_data

    # create the records.
    obj_db.create_multiple_records(list_obj_exp)

    # get the records from the mock table.
    retrieved_exp1 = obj_db.read_one_by_id("11111111-1111-2222-3333-44444444444444")
    retrieved_exp2 = obj_db.read_one_by_id("22222222-1111-2222-3333-44444444444444")

    # run the tests.
    assert retrieved_exp1.title == "Jane Smith Experience"
    assert retrieved_exp2.title == "Baby Smith Experience"


def test_retrieve_record(data_table, data_table_with_data):
    """
    Test the read_one_by_id function.
    :param data_table: mock table.
    :param data_table_with_data: mock table with data.
    """
    # set the id to be the same as the mock table in the fixture.
    db_id = 'abcd-1234'

    # create the dynamo db object.
    obj_db = DynamoDb()

    # overwrite the table with the mock table.
    obj_db.table = data_table_with_data

    # get the result as experience obj for this id.
    obj_result = obj_db.read_one_by_id(db_id)

    # run the test
    assert obj_result.title == "title1"


def test_delete_record(data_table, data_table_with_data):
    """
    Test the delete_by_id function.
    :param data_table: mock table.
    :param data_table_with_data: mock table with data.
    """
    # set the id to be the same as the mock table in the fixture.
    db_id = 'abcd-1234'

    # create the dynamo db object.
    obj_db = DynamoDb()

    # overwrite the table with the mock table.
    obj_db.table = data_table_with_data

    # run the test
    assert obj_db.delete_by_id(db_id) is True
