import pytest
from pktscrape.module_db import DynamoDb
from pktscrape.module_scraping import Experience


def test_create_record():

    # create an object and set the values.
    obj_exp = Experience()
    obj_exp.uuid = "00000000-1111-2222-3333-44444444444444"
    obj_exp.title = "John Smith Experience"
    obj_exp.classification = "Currently Taking"
    obj_exp.description = "This is a test description"

    # using db object.
    obj_db = DynamoDb()

    # run the test
    assert obj_db.create_record(obj_exp) is True


def test_retrieve_record():

    # set the id to be the same as the create record test.
    db_id = '00000000-1111-2222-3333-44444444444444'

    # create the dynamo db object.
    obj_db = DynamoDb()

    # get the result as experience obj for this id.
    obj_result = obj_db.read_one_by_id(db_id)

    # run the test
    assert obj_result.title == "John Smith Experience"


def test_delete_record():

    # set the id to be the same as the create record test.
    db_id = '00000000-1111-2222-3333-44444444444444'

    # create the dynamo db object.
    obj_db = DynamoDb()

    # run the test
    assert obj_db.delete_by_id(db_id) is True
