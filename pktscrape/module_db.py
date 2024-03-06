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
        self.dynamodb = boto3.resource('dynamodb',
                                       region_name=cfg.AWS_REGION)
        self.table = self.dynamodb.Table(cfg.DB_TABLE)

    def create_record(self, obj_exp):
        """
        Creates a new record in Dynamo DB based on the properties
        of the Experience object passed to it.

        :param obj_exp: Experience object.
        :return: boolean to indicate success or failure.
        """

        # add the item.
        self.table.put_item(
            Item={
                'uuid': obj_exp.uuid,
                'title': obj_exp.title,
                'classification': obj_exp.classification,
                'description': obj_exp.description
            }
        )

        # return success here.
        return True

    def create_multiple_records(self, list_obj_exp):
        """
        Creates multiple records in Dynamo DB based on the properties
        of the Experience objects passed to it.

        :param list_obj_exp: List of Experience objects.
        :return: boolean to indicate success or failure.
        """

        # loop through the list and add the items.
        for obj_exp in list_obj_exp:
            self.table.put_item(
                Item={
                    'uuid': obj_exp.uuid,
                    'title': obj_exp.title,
                    'classification': obj_exp.classification,
                    'description': obj_exp.description
                }
            )

        # return success here.
        return True

    def read_one_by_id(self, uuid):
        """
        Retrieves a single record from the dynamodb database
        based on an id. Returns an experience object.

        :param uuid: id of record as a string.
        :return: Experience object.
        """
        # object that will be returned.
        obj_return = Experience()

        response = self.table.query(
            KeyConditionExpression=Key('uuid').eq(uuid)
        )

        # get the results.
        arr_items = response['Items']

        # loop through the results but there really
        # should only be one.
        for item in arr_items:
            obj_return.uuid = item["uuid"]
            obj_return.title = item["title"]
            obj_return.description = item["description"]
            obj_return.classification = item["classification"]

        # return the result as an object
        # return response['Items']
        return obj_return

    def delete_by_id(self, record_id):
        """
        Deletes a record from the dynamodb database based on an id.
        :param record_id: id of record as a string.
        :return: boolean to indicate success or failure.
        """

        # delete the item and get the response.
        response = self.table.delete_item(
            Key={"uuid": record_id}
        )

        # return success here.
        return True
