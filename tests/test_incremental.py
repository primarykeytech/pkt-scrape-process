import pytest

from pktscrape.incremental import run_incremental_demo
from pktscrape.models import Experience


HTML_AB = '<div class="experience">Alpha</div><div class="experience">Bravo</div>'
HTML_ABC_CHANGED = '<div class="experience">Alpha</div><div class="experience">Bravo updated</div><div class="experience">Charlie</div>'


def test_incremental_first_and_identical_rerun(tmp_path):
    first = run_incremental_demo(tmp_path, HTML_AB)
    second = run_incremental_demo(tmp_path, HTML_AB)

    assert (first.new, first.changed, first.unchanged, first.records) == (2, 0, 0, 2)
    assert (second.new, second.changed, second.unchanged, second.records) == (0, 0, 2, 2)


def test_incremental_detects_changed_and_new_records(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    result = run_incremental_demo(tmp_path, HTML_ABC_CHANGED)

    assert (result.new, result.changed, result.unchanged, result.records) == (1, 1, 1, 3)


def test_content_hash_is_deterministic_and_independent_of_record_identity():
    first = Experience.from_content(record_id="source:1", title="title", classification="class", description="same")
    second = Experience.from_content(record_id="another:1", title="title", classification="class", description="same")

    assert first.uuid != second.uuid
    assert first.content_hash == second.content_hash


def test_failure_keeps_previous_publication_and_retry_matches_clean_run(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    previous_csv = (tmp_path / "experiences.csv").read_bytes()

    with pytest.raises(RuntimeError):
        run_incremental_demo(tmp_path, HTML_ABC_CHANGED, fail_before_publish=True)

    assert (tmp_path / "experiences.csv").read_bytes() == previous_csv
    retry = run_incremental_demo(tmp_path, HTML_ABC_CHANGED)
    clean = run_incremental_demo(tmp_path / "clean", HTML_ABC_CHANGED)

    assert (retry.new, retry.changed, retry.unchanged, retry.records) == (1, 1, 1, 3)
    assert (clean.new, clean.changed, clean.unchanged, clean.records) == (3, 0, 0, 3)
    assert (tmp_path / "experiences.csv").read_bytes() == (tmp_path / "clean" / "experiences.csv").read_bytes()
