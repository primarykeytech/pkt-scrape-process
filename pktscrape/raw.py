"""Immutable local raw-input batches and offline replay."""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .incremental import IncrementalResult, run_incremental_demo

PARSER_VERSION = "html-experience-v1"
SCHEMA_VERSION = "raw-batch-v1"


def capture_batch(
    root: str | Path,
    html: str,
    *,
    source_url: str,
    source_id: str,
    parser_version: str = PARSER_VERSION,
) -> Path:
    batch = Path(root) / uuid.uuid4().hex
    batch.mkdir(parents=True)
    raw = html.encode("utf-8")
    (batch / "input.html").write_bytes(raw)
    manifest = {
        "batch_id": batch.name,
        "source_id": source_id,
        "source_url": source_url,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "encoding": "utf-8",
        "input_path": "input.html",
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "capture_parser_version": parser_version, "schema_version": SCHEMA_VERSION,
    }
    (batch / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return batch


def replay_batch(
    batch_dir: str | Path, output_dir: str | Path, *, parser_version: str = PARSER_VERSION
) -> IncrementalResult:
    batch = Path(batch_dir).resolve()
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {"batch_id": str, "source_id": str, "source_url": str, "captured_at_utc": str, "encoding": str, "input_path": str, "content_sha256": str, "capture_parser_version": str, "schema_version": str}
    if manifest.get("schema_version") != SCHEMA_VERSION or any(not isinstance(manifest.get(k), typ) or not manifest[k] for k, typ in required.items()):
        raise ValueError("invalid raw batch manifest")
    if manifest["encoding"].lower() != "utf-8":
        raise ValueError("raw batches are UTF-8 only")
    if manifest["batch_id"] != batch.name or len(manifest["content_sha256"]) != 64:
        raise ValueError("invalid raw batch identity or hash")
    captured_at = datetime.fromisoformat(manifest["captured_at_utc"])
    if captured_at.tzinfo is None or captured_at.utcoffset().total_seconds() != 0:
        raise ValueError("capture timestamp must be UTC")
    declared = Path(manifest["input_path"])
    if declared.is_absolute():
        raise ValueError("input path must be relative")
    candidate = (batch / declared).resolve()
    if batch not in candidate.parents or candidate.name != "input.html":
        raise ValueError("input path escapes batch")
    raw = candidate.read_bytes()
    if hashlib.sha256(raw).hexdigest() != manifest["content_sha256"]:
        raise ValueError("raw input hash mismatch")
    return run_incremental_demo(output_dir, raw.decode(manifest["encoding"]), source_id=manifest["source_id"], provenance={"batch_id": manifest["batch_id"], "source_id": manifest["source_id"], "capture_parser_version": manifest["capture_parser_version"], "replay_parser_version": parser_version, "schema_version": SCHEMA_VERSION})
