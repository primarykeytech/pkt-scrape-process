"""Backward-compatible DynamoDB facade; new callers use ``storage`` directly."""

from . import config
from .models import Experience
from .storage import DynamoExperienceRepository


class DynamoDb(DynamoExperienceRepository):
    def __init__(self):
        super().__init__(config.DB_TABLE, region_name=config.AWS_REGION)

    def create_record(self, obj_exp: Experience) -> bool:
        self.save(obj_exp)
        return True

    def create_multiple_records(self, list_obj_exp: list[Experience]) -> bool:
        self.save_many(list_obj_exp)
        return True

    def read_one_by_id(self, uuid: str) -> Experience | None:
        return self.get(uuid)

    def delete_by_id(self, record_id: str) -> bool:
        self.table.delete_item(Key={"uuid": record_id})
        return True
