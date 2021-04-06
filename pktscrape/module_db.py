import boto3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cfg


class DynamoDb:
    """
    The purpose of the DynamoDb class is to handle interactions with
    the DynamoDB database. Relies on boto3.
    """
    def __init__(self):
        pass

    def create_record(self, objExp):
        """
        Creates a new record in Dynamo DB based on the properties
        of the Experience object passed to it.

        :param objExp: Experience object.
        :return:
        """

        # create the boto3 object.
        dynamodb = boto3.resource('dynamodb',
                                  region_name=cfg.AWS_REGION)

        # set the table from the cfg file.
        table = dynamodb.Table(cfg.DB_TABLE)

        # add the item.
        table.put_item(
            Item={
                'id': objExp.uuid,
                'title': objExp.title,
                'classification': objExp.classification,
                'description': objExp.description
            }
        )

        # return success here.
        # TODO: yeah, we're going to need some error trapping.
        return True
