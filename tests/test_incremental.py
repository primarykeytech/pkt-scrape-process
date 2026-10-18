import pytest

from pktscrape.incremental import current_snapshot, run_incremental_demo
from pktscrape.models import Experience


HTML_AB = '<div class="experience" data-record-id="a">Alpha</div><div class="experience" data-record-id="b">Bravo</div>'
HTML_ABC_CHANGED = '<div class="experience" data-record-id="a">Alpha</div><div class="experience" data-record-id="b">Bravo updated</div><div class="experience" data-record-id="c">Charlie</div>'


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
    previous = current_snapshot(tmp_path)

    with pytest.raises(RuntimeError):
        run_incremental_demo(tmp_path, HTML_ABC_CHANGED, fail_before_pointer=True)

    assert current_snapshot(tmp_path) == previous
    retry = run_incremental_demo(tmp_path, HTML_ABC_CHANGED)
    clean = run_incremental_demo(tmp_path / "clean", HTML_ABC_CHANGED)

    assert (retry.new, retry.changed, retry.unchanged, retry.records) == (1, 1, 1, 3)
    assert (clean.new, clean.changed, clean.unchanged, clean.records) == (3, 0, 0, 3)
    assert (current_snapshot(tmp_path) / "experiences.csv").read_bytes() == (current_snapshot(tmp_path / "clean") / "experiences.csv").read_bytes()


def test_reordering_and_prepending_are_not_changes(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    result = run_incremental_demo(tmp_path, '<div class="experience" data-record-id="c">Charlie</div><div class="experience" data-record-id="b">Bravo</div><div class="experience" data-record-id="a">Alpha</div>')
    assert (result.new, result.changed, result.unchanged, result.application_writes) == (1, 0, 2, 1)


def test_duplicate_ids_fail_before_publication(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    previous = current_snapshot(tmp_path)
    with pytest.raises(ValueError):
        run_incremental_demo(tmp_path, '<div class="experience" data-record-id="a">one</div><div class="experience" data-record-id="a">two</div>')
    assert current_snapshot(tmp_path) == previous


def test_failure_after_pointer_keeps_complete_generation_and_retry_converges(tmp_path):
    run_incremental_demo(tmp_path, HTML_AB)
    with pytest.raises(RuntimeError):
        run_incremental_demo(tmp_path, HTML_ABC_CHANGED, fail_after_pointer=True)
    published = current_snapshot(tmp_path)
    assert (published / "experiences.parquet").is_file()
    retry = run_incremental_demo(tmp_path, HTML_ABC_CHANGED)
    assert (retry.new, retry.changed, retry.unchanged, retry.records) == (0, 0, 3, 3)


def test_pointer_replacement_failure_preserves_prior_snapshot_and_retry(tmp_path, monkeypatch):
    run_incremental_demo(tmp_path, HTML_AB)
    previous = current_snapshot(tmp_path)
    previous_csv = (previous / "experiences.csv").read_bytes()
    from pktscrape import incremental

    actual_replace = incremental.os.replace

    def fail_pointer(source, destination):
        if Path(destination).name == "current.json":
            raise OSError("simulated pointer replacement failure")
        actual_replace(source, destination)

    monkeypatch.setattr(incremental.os, "replace", fail_pointer)
    with pytest.raises(OSError):
        run_incremental_demo(tmp_path, HTML_ABC_CHANGED)
    assert current_snapshot(tmp_path) == previous
    assert (current_snapshot(tmp_path) / "experiences.csv").read_bytes() == previous_csv
    monkeypatch.setattr(incremental.os, "replace", actual_replace)
    assert run_incremental_demo(tmp_path, HTML_ABC_CHANGED).records == 3
