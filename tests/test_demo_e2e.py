from pktscrape.demo import run_demo


def test_offline_demo_creates_portable_artifacts(tmp_path):
    result = run_demo(tmp_path)
    assert result["records"] == 3
    assert result["csv"].is_file()
    assert result["parquet"].is_file()
    assert result["wordcloud"].is_file()
    assert "synthetic-demo" in result["csv"].read_text(encoding="utf-8")
