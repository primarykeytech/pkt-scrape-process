"""Package-safe configuration defaults for compatibility adapters."""

from os import getenv

BASE_URL = getenv("PKT_BASE_URL", "https://example.invalid")
CLASSIFICATION = getenv("PKT_CLASSIFICATION", "unclassified")
AWS_REGION = getenv("AWS_REGION", "us-west-2")
DB_TABLE = getenv("PKT_DB_TABLE", "pkt-scrape-demo")
IDENTIFY_CONTENT = getenv("PKT_CONTENT_CLASS", "ddc-comment")
