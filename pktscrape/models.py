"""Domain types shared by ingestion, storage, and export."""

from dataclasses import asdict, dataclass
from uuid import uuid4


@dataclass(slots=True)
class Experience:
    """A normalized experience extracted from one approved source page."""

    uuid: str = ""
    title: str = ""
    classification: str = ""
    description: str = ""

    @classmethod
    def create(cls, *, title: str, classification: str, description: str) -> "Experience":
        if not title.strip() or not classification.strip() or not description.strip():
            raise ValueError("Experience title, classification, and description are required")
        return cls(str(uuid4()), title, classification, description)

    def to_item(self) -> dict[str, str]:
        return asdict(self)
