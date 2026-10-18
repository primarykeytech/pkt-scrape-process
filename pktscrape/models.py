"""Domain types shared by ingestion, storage, and export."""

from dataclasses import asdict, dataclass
from hashlib import sha256
from uuid import uuid4


@dataclass(slots=True)
class Experience:
    """A normalized experience extracted from one approved source page."""

    uuid: str = ""
    title: str = ""
    classification: str = ""
    description: str = ""
    content_hash: str = ""

    @classmethod
    def create(cls, *, title: str, classification: str, description: str) -> "Experience":
        if not title.strip() or not classification.strip() or not description.strip():
            raise ValueError("Experience title, classification, and description are required")
        return cls(str(uuid4()), title, classification, description)

    def to_item(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_content(
        cls, *, record_id: str, title: str, classification: str, description: str
    ) -> "Experience":
        if not all((record_id.strip(), title.strip(), classification.strip(), description.strip())):
            raise ValueError("Experience identity and content are required")
        payload = "\x1f".join((title, classification, description)).encode("utf-8")
        return cls(record_id, title, classification, description, sha256(payload).hexdigest())
