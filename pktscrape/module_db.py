import boto3
from boto3.dynamodb.conditions import Key
from module_scraping import Experience
import os
import sys
import cfg
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class DynamoDb:
    """
    The purpose of the DynamoDb class is to handle interactions with
    the DynamoDB database. Relies on boto3.
    """
    def __init__(self):
        pass

    def create_record(self, obj_exp):
        """
        Creates a new record in Dynamo DB based on the properties
        of the Experience object passed to it.

        :param obj_exp: Experience object.
        :return: boolean to indicate success or failure.
        """

        # create the boto3 object.
        dynamodb = boto3.resource('dynamodb',
                                  region_name=cfg.AWS_REGION)

        # set the table from the cfg file.
        table = dynamodb.Table(cfg.DB_TABLE)

        # add the item.
        table.put_item(
            Item={
                'id': obj_exp.uuid,
                'title': obj_exp.title,
                'classification': obj_exp.classification,
                'description': obj_exp.description
            }
        )

        # return success here.
        # TODO: yeah, we're going to need some error trapping.
        return True

    def read_one_by_id(self, id):
        """
        Retrieves a single record from the dynamodb database
        based on an id. Returns an experience object.

        :param id: id of record as a string.
        :return: Experience object.
        """
        # object that will be returned.
        obj_return = Experience()

        # create the boto3 object.
        dynamodb = boto3.resource('dynamodb',
                                  region_name=cfg.AWS_REGION)
        table = dynamodb.Table(cfg.DB_TABLE)
        response = table.query(
            KeyConditionExpression=Key('id').eq(id)
        )

        # get the results.
        arr_items = response['Items']

        # loop through the results but there really
        # should only be one.
        for item in arr_items:
            obj_return.uuid = item["id"]
            obj_return.title = item["title"]
            obj_return.description = item["description"]
            obj_return.classification = item["classification"]

        # return the result as an object
        # return response['Items']
        return obj_return

    def delete_by_id(self, record_id):

        # create the boto3 object and set the table.
        dynamodb = boto3.resource('dynamodb',
                                  region_name=cfg.AWS_REGION)
        table = dynamodb.Table(cfg.DB_TABLE)

        # delete the item and get the response.
        response = table.delete_item(
            Key={
                "id": record_id
            }
        )

        # return success here.
        # TODO: yeah, we're going to need some error trapping.
        return True
