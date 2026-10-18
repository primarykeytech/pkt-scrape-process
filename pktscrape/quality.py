"""Small, versioned quality gate with visible quarantines."""

from collections import Counter
from dataclasses import dataclass

from .models import Experience

POLICY_VERSION = "quality-v1"


@dataclass(frozen=True)
class QualityPolicy:
    rejection_threshold: int = 0
    max_description_length: int = 10000

    def __post_init__(self):
        if (
            type(self.rejection_threshold) is not int
            or type(self.max_description_length) is not int
            or self.rejection_threshold < 0
            or self.max_description_length < 1
        ):
            raise ValueError("invalid quality policy range")


def assess(records: list[Experience], policy: QualityPolicy) -> tuple[list[Experience], list[dict]]:
    accepted, rejected = [], []
    id_counts = Counter(record.uuid for record in records if record.uuid)
    duplicate_ids = {record_id for record_id, count in id_counts.items() if count > 1}
    for record in records:
        reason = None
        if record.uuid in duplicate_ids:
            # Check duplicates first so an invalid first occurrence cannot make a
            # later valid occurrence appear unique.
            reason = "duplicate_record_id"
        elif not all(
            (
                record.uuid.strip(),
                record.title.strip(),
                record.classification.strip(),
                record.description.strip(),
            )
        ):
            reason = "required_field_missing"
        elif len(record.description) > policy.max_description_length:
            reason = "description_too_long"
        if reason:
            rejected.append(
                {
                    "reason_code": reason,
                    "record_id": record.uuid,
                    "raw_record_reference": record.uuid,
                    "details": {"description_length": len(record.description)},
                }
            )
        else:
            accepted.append(record)
    return accepted, rejected
