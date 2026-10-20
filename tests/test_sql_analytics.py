import json
import subprocess
import sys

import pytest

from pktscrape.incremental import current_snapshot, run_incremental_demo
from pktscrape.quality import QualityPolicy
from pktscrape.sql_analytics import analyze_published_snapshot


HTML_AB = (
    '<div class="experience" data-record-id="a">Alpha</div>'
    '<div class="experience" data-record-id="b">Bravo</div>'
)
HTML_ABC = HTML_AB + '<div class="experience" data-record-id="c">Charlie</div>'


def test_analytics_reports_one_published_generation_and_is_read_only(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB, provenance={"batch_id": "batch-1"})
    snapshot = current_snapshot(tmp_path)
    before = {
        path.name: path.read_bytes()
        for path in (snapshot / "experiences.parquet", snapshot / "state.json")
    }

    first = analyze_published_snapshot(tmp_path)
    second = analyze_published_snapshot(tmp_path)

    assert first.to_dict() == second.to_dict()
    assert first.snapshot == snapshot
    assert first.summary == {
        "records": 2,
        "distinct_record_ids": 2,
        "distinct_contents": 2,
        "average_description_characters": 5.0,
    }
    assert first.by_classification == [
        {
            "classification": "synthetic-demo",
            "records": 2,
            "distinct_contents": 2,
            "average_description_characters": 5.0,
        }
    ]
    assert first.provenance == {"batch_id": "batch-1"}
    assert first.quality == {"policy_version": "quality-v1", "accepted": 2, "rejected": 0}
    assert before == {
        path.name: path.read_bytes()
        for path in (snapshot / "experiences.parquet", snapshot / "state.json")
    }


def test_analytics_follows_changed_published_generation(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    first = analyze_published_snapshot(tmp_path)
    run_incremental_demo(tmp_path, HTML_ABC)
    second = analyze_published_snapshot(tmp_path)

    assert first.snapshot != second.snapshot
    assert first.summary["records"] == 2
    assert second.summary["records"] == 3
    assert second.quality["accepted"] == 3


def test_analytics_rejects_missing_invalid_or_incomplete_publication(tmp_path):
    with pytest.raises(ValueError, match="pointer is missing"):
        analyze_published_snapshot(tmp_path)

    (tmp_path / "current.json").write_text("not-json", encoding="utf-8")
    with pytest.raises(ValueError, match="pointer is invalid"):
        analyze_published_snapshot(tmp_path)

    (tmp_path / "current.json").unlink()
    run_incremental_demo(tmp_path, HTML_AB)
    snapshot = current_snapshot(tmp_path)
    (snapshot / "experiences.parquet").unlink()
    with pytest.raises(ValueError, match="Parquet export is missing"):
        analyze_published_snapshot(tmp_path)


@pytest.mark.parametrize(
    "state",
    [
        {},
        {"records": {}, "provenance": {}, "quality": {}},
        {
            "records": [],
            "provenance": {},
            "quality": {"policy_version": "quality-v1", "accepted": 0, "rejected": 0},
        },
        {
            "records": {},
            "provenance": [],
            "quality": {"policy_version": "quality-v1", "accepted": 0, "rejected": 0},
        },
        {
            "records": {},
            "provenance": {},
            "quality": {"policy_version": "quality-v1", "accepted": True, "rejected": 0},
        },
    ],
)
def test_analytics_rejects_incomplete_or_corrupt_published_state(tmp_path, state):
    run_incremental_demo(tmp_path, HTML_AB)
    snapshot = current_snapshot(tmp_path)
    (snapshot / "state.json").write_text(json.dumps(state), encoding="utf-8")

    with pytest.raises(ValueError, match="published snapshot state is invalid"):
        analyze_published_snapshot(tmp_path)


def test_analytics_cli_fails_before_output_for_corrupt_state(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    snapshot = current_snapshot(tmp_path)
    (snapshot / "state.json").write_text("{}", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "-m", "pktscrape", "analytics", "--output", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert completed.stdout == ""
    assert "published snapshot state is invalid" in completed.stderr


def test_analytics_excludes_rejected_records(tmp_path):
    result = run_incremental_demo(
        tmp_path,
        '<div class="experience" data-record-id="good">good</div>'
        '<div class="experience" data-record-id="bad"></div>',
        policy=QualityPolicy(rejection_threshold=1),
    )

    analytics = analyze_published_snapshot(tmp_path)

    assert result.records == 1
    assert analytics.summary["records"] == 1
    assert analytics.quality == {"policy_version": "quality-v1", "accepted": 1, "rejected": 1}


def test_analytics_cli_emits_json_for_the_current_snapshot(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)

    completed = subprocess.run(
        [sys.executable, "-m", "pktscrape", "analytics", "--output", str(tmp_path)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["summary"]["records"] == 2
    assert report["snapshot"] == str(current_snapshot(tmp_path))
