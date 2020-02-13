import boto3
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import cfg


class DynamoDb:

    def __init__(self):
        pass

    def create_record(self, objExp):

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


