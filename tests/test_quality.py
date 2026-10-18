import json
import subprocess
import sys

import pytest

from pktscrape.incremental import current_snapshot, run_incremental_demo
from pktscrape.models import Experience
from pktscrape.quality import QualityPolicy, assess
from pktscrape.raw import capture_batch, replay_batch


def test_quality_required_duplicate_bounds_and_threshold_ranges():
    valid = Experience.from_content(record_id="a", title="t", classification="c", description="ok")
    invalid = Experience(uuid="", title="", classification="c", description="x")
    duplicate = Experience.from_content(
        record_id="a", title="t", classification="c", description="different"
    )
    accepted, rejected = assess(
        [valid, invalid, duplicate], QualityPolicy(max_description_length=2)
    )
    assert not accepted
    assert [item["reason_code"] for item in rejected] == [
        "duplicate_record_id",
        "required_field_missing",
        "duplicate_record_id",
    ]
    for field, value in (
        ("rejection_threshold", -1),
        ("rejection_threshold", True),
        ("rejection_threshold", 1.5),
        ("rejection_threshold", float("nan")),
        ("rejection_threshold", float("inf")),
        ("rejection_threshold", "1"),
        ("rejection_threshold", None),
        ("max_description_length", 0),
        ("max_description_length", False),
        ("max_description_length", float("nan")),
        ("max_description_length", float("inf")),
        ("max_description_length", 1.5),
        ("max_description_length", "1"),
        ("max_description_length", None),
    ):
        with pytest.raises(ValueError):
            QualityPolicy(**{field: value})


def test_duplicate_ids_quarantine_invalid_and_valid_occurrences_regardless_of_order():
    invalid_first = Experience(uuid="same", title="", classification="c", description="bad")
    valid_second = Experience.from_content(
        record_id="same", title="t", classification="c", description="good"
    )
    accepted, rejected = assess([invalid_first, valid_second], QualityPolicy())
    assert not accepted
    assert [item["reason_code"] for item in rejected] == [
        "duplicate_record_id",
        "duplicate_record_id",
    ]


def test_quality_gate_preserves_snapshot_and_allowed_threshold_publishes(tmp_path, monkeypatch):
    run_incremental_demo(tmp_path, '<div class="experience" data-record-id="a">ok</div>')
    before = current_snapshot(tmp_path)
    from pktscrape import incremental

    bad = Experience(uuid="", title="", classification="c", description="bad")
    good = Experience.from_content(record_id="b", title="t", classification="c", description="good")
    monkeypatch.setattr(incremental.OfflineHtmlSource, "experiences", lambda _self: [bad, good])
    with pytest.raises(ValueError):
        run_incremental_demo(tmp_path, "ignored")
    assert current_snapshot(tmp_path) == before
    assert run_incremental_demo(tmp_path, "ignored", policy=QualityPolicy(1)).records == 2
    assert any(
        "required_field_missing" in path.read_text()
        for path in (tmp_path / "quality-failures").glob("*.json")
    )


def test_replay_quality_failure_retains_snapshot_and_records_raw_provenance(tmp_path):
    raw_root = tmp_path / "raw"
    output = tmp_path / "out"
    good = capture_batch(
        raw_root,
        '<div class="experience" data-record-id="a">good</div>',
        source_url="https://example.test/source",
        source_id="source",
    )
    replay_batch(good, output)
    before = current_snapshot(output)

    bad = capture_batch(
        raw_root,
        '<div class="experience" data-record-id="bad"></div>',
        source_url="https://example.test/source",
        source_id="source",
    )
    with pytest.raises(ValueError, match="requires accepted records: all_records_rejected"):
        replay_batch(bad, output)
    assert current_snapshot(output) == before

    diagnostic = next(
        json.loads(path.read_text())
        for path in (output / "quality-failures").glob("*.json")
        if json.loads(path.read_text())["provenance"].get("batch_id") == bad.name
    )
    assert diagnostic["accepted"] == 0
    assert diagnostic["rejected"][0]["reason_code"] == "required_field_missing"
    assert diagnostic["rejected"][0]["raw_record_reference"] == '["source","bad"]'
    assert diagnostic["provenance"] == {
        "batch_id": bad.name,
        "source_id": "source",
        "source_url": "https://example.test/source",
        "content_sha256": json.loads((bad / "manifest.json").read_text())["content_sha256"],
        "input_path": "input.html",
        "capture_parser_version": "html-experience-v1",
        "replay_parser_version": "html-experience-v1",
        "schema_version": "raw-batch-v1",
    }

    corrected = capture_batch(
        raw_root,
        '<div class="experience" data-record-id="bad">corrected</div>',
        source_url="https://example.test/source",
        source_id="source",
    )
    assert replay_batch(corrected, output).records == 2


def test_empty_batch_is_rejected_and_preserves_snapshot(tmp_path):
    run_incremental_demo(tmp_path, '<div class="experience">good</div>')
    before = current_snapshot(tmp_path)
    with pytest.raises(ValueError, match="requires accepted records: empty_batch"):
        run_incremental_demo(tmp_path, "<p>no candidates</p>")
    assert current_snapshot(tmp_path) == before
    assert any(
        '"batch_rejection_reason": "empty_batch"' in path.read_text()
        for path in (tmp_path / "quality-failures").glob("*.json")
    )


@pytest.mark.parametrize("seed_snapshot", [False, True])
def test_all_rejected_batch_is_always_fatal_and_preserves_snapshot(tmp_path, seed_snapshot):
    if seed_snapshot:
        run_incremental_demo(tmp_path, '<div class="experience">good</div>')
    before = current_snapshot(tmp_path)
    with pytest.raises(ValueError, match="requires accepted records: all_records_rejected"):
        run_incremental_demo(
            tmp_path,
            '<div class="experience" data-record-id="bad"></div>',
            policy=QualityPolicy(rejection_threshold=99),
        )
    assert current_snapshot(tmp_path) == before
    assert any(
        '"batch_rejection_reason": "all_records_rejected"' in path.read_text()
        for path in (tmp_path / "quality-failures").glob("*.json")
    )


def test_replay_cli_threshold_rejects_mixed_batch_by_default_and_accepts_explicit_one(tmp_path):
    batch = capture_batch(
        tmp_path / "raw",
        '<div class="experience" data-record-id="good">good</div>'
        '<div class="experience" data-record-id="bad"></div>',
        source_url="https://example.test/source",
        source_id="source",
    )
    default = subprocess.run(
        [
            sys.executable,
            "-m",
            "pktscrape",
            "replay",
            str(batch),
            "--output",
            str(tmp_path / "default"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert default.returncode != 0
    assert "quality rejection threshold exceeded" in default.stderr

    accepted_output = tmp_path / "accepted"
    accepted = subprocess.run(
        [
            sys.executable,
            "-m",
            "pktscrape",
            "replay",
            str(batch),
            "--output",
            str(accepted_output),
            "--rejection-threshold",
            "1",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert accepted.returncode == 0, accepted.stderr
    assert "records=1" in accepted.stdout
    assert current_snapshot(accepted_output)
