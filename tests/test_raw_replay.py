import json
from pathlib import Path

import pytest

from pktscrape.incremental import current_snapshot
from pktscrape.models import Experience
from pktscrape.raw import capture_batch, replay_batch


HTML = '<div class="experience" data-record-id="a">Alpha</div>'


def test_capture_and_offline_replay_metadata_and_hash(tmp_path):
    batch = capture_batch(
        tmp_path / "raw", HTML, source_url="https://example.test/a", source_id="a"
    )
    manifest = json.loads((batch / "manifest.json").read_text())
    assert manifest["captured_at_utc"].endswith("+00:00") and len(manifest["content_sha256"]) == 64
    assert replay_batch(batch, tmp_path / "out", parser_version="parser-v2").records == 1
    provenance = json.loads((current_snapshot(tmp_path / "out") / "state.json").read_text())[
        "provenance"
    ]
    assert provenance["capture_parser_version"] == "html-experience-v1"
    assert provenance["replay_parser_version"] == "parser-v2"


def test_corrupt_or_escape_input_keeps_previous_snapshot(tmp_path):
    batch = capture_batch(tmp_path / "raw", HTML, source_url="x", source_id="a")
    replay_batch(batch, tmp_path / "out")
    before = current_snapshot(tmp_path / "out")
    manifest = json.loads((batch / "manifest.json").read_text())
    manifest["input_path"] = "../outside.html"
    (batch / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        replay_batch(batch, tmp_path / "out")
    assert current_snapshot(tmp_path / "out") == before


def test_missing_or_absolute_input_is_rejected_before_replay(tmp_path):
    batch = capture_batch(tmp_path / "raw", HTML, source_url="x", source_id="a")
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["input_path"] = str(batch / "input.html")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        replay_batch(batch, tmp_path / "out")
    manifest["input_path"] = "input.html"
    manifest_path.write_text(json.dumps(manifest))
    (batch / "input.html").unlink()
    with pytest.raises(FileNotFoundError):
        replay_batch(batch, tmp_path / "out")


def test_unknown_manifest_schema_is_fatal_before_replay(tmp_path):
    batch = capture_batch(tmp_path / "raw", HTML, source_url="x", source_id="a")
    output = tmp_path / "out"
    replay_batch(batch, output)
    before = current_snapshot(output)
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = "raw-batch-v999"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="invalid raw batch manifest"):
        replay_batch(batch, output)
    assert current_snapshot(output) == before


def test_two_sources_with_same_source_record_id_do_not_collide(tmp_path):
    first = capture_batch(tmp_path / "raw", HTML, source_url="x", source_id="source-a")
    second = capture_batch(tmp_path / "raw", HTML, source_url="y", source_id="source-b")
    replay_batch(first, tmp_path / "out")
    assert replay_batch(second, tmp_path / "out").records == 2


def test_non_utc_timestamp_and_network_disabled_replay_are_safe(tmp_path, monkeypatch):
    batch = capture_batch(tmp_path / "raw", HTML, source_url="x", source_id="a")
    manifest_path = batch / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["captured_at_utc"] = "2026-01-01T00:00:00+01:00"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        replay_batch(batch, tmp_path / "out")
    manifest["captured_at_utc"] = "2026-01-01T00:00:00+00:00"
    manifest_path.write_text(json.dumps(manifest))
    monkeypatch.setattr("requests.get", lambda *_args, **_kwargs: pytest.fail("network used"))
    assert replay_batch(batch, tmp_path / "out").records == 1


def test_utf8_and_semantic_parser_replay(tmp_path, monkeypatch):
    batch = capture_batch(
        tmp_path / "raw",
        "<div class='experience' data-record-id='a'>café</div>",
        source_url="x",
        source_id="a",
    )
    raw_before = (batch / "input.html").read_bytes()
    replay_batch(batch, tmp_path / "out")
    manifest = json.loads((batch / "manifest.json").read_text())
    manifest["encoding"] = "latin-1"
    (batch / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        replay_batch(batch, tmp_path / "out")
    manifest["encoding"] = "utf-8"
    (batch / "manifest.json").write_text(json.dumps(manifest))
    from pktscrape import incremental

    monkeypatch.setattr(
        incremental.OfflineHtmlSource,
        "experiences",
        lambda _self: [
            Experience.from_content(
                record_id='["a","a"]',
                title="a",
                classification="synthetic-demo",
                description="parser changed",
            )
        ],
    )
    assert replay_batch(batch, tmp_path / "out", parser_version="parser-v2").changed == 1
    assert (batch / "input.html").read_bytes() == raw_before
