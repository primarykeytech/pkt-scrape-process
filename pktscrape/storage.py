"""Persistence adapters for normalized experiences."""

from collections.abc import Iterable

import boto3

from .models import Experience


class DynamoExperienceRepository:
    """Small DynamoDB adapter; accepts an injected table for local tests."""

    def __init__(self, table_name: str | None = None, *, region_name: str = "us-west-2", table=None):
        self.table = table or boto3.resource("dynamodb", region_name=region_name).Table(table_name)

    def save(self, experience: Experience) -> None:
        if not all((experience.uuid.strip(), experience.title.strip(), experience.classification.strip(), experience.description.strip())):
            raise ValueError("Refusing to persist an incomplete Experience")
        self.table.put_item(Item=experience.to_item())

    def save_many(self, experiences: Iterable[Experience]) -> int:
        count = 0
        for experience in experiences:
            self.save(experience)
            count += 1
        return count

    def get(self, record_id: str) -> Experience | None:
        item = self.table.get_item(Key={"uuid": record_id}).get("Item")
        return Experience(**item) if item else None

    def list_all(self, *, page_size: int = 100) -> list[Experience]:
        items: list[Experience] = []
        scan_args: dict[str, object] = {"Limit": page_size}
        while True:
            response = self.table.scan(**scan_args)
            items.extend(Experience(**item) for item in response.get("Items", []))
            key = response.get("LastEvaluatedKey")
            if not key:
                return items
            scan_args["ExclusiveStartKey"] = key
