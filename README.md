# pkt-scrape-process

An offline-first, explainable data-pipeline demonstration. It shows synthetic HTML ingestion,
typed records, DynamoDB-style storage, CSV/Parquet export, bounded Spark analysis, and a word
cloud—without scraping a live site or requiring AWS credentials.

## Quick start (offline and safe)

Python 3.12+ is required. Create a virtual environment and install the project:

```powershell
python -m pip install -e ".[dev]"
python -m pktscrape demo --output artifacts/demo
```

The base install is the complete offline demo. Spark is deliberately optional:
`python -m pip install -e ".[spark]"`. It also requires a compatible JDK and is not needed for
the command above.

The command uses only built-in synthetic HTML and Moto's in-memory DynamoDB simulation. It creates:

- `experiences.csv`
- `experiences.parquet`
- `wordcloud.png`

Run the verification suite with `pytest -q`. The end-to-end test covers HTML -> typed records ->
Moto DynamoDB -> CSV/Parquet -> PNG.

## Incremental processing and safe reruns

Run `python -m pktscrape incremental-demo --output artifacts/incremental-demo` twice. The first run
reports `new=3 changed=0 unchanged=0 records=3`; the second reports
`new=0 changed=0 unchanged=3 records=3`. The demo's `.incremental-state.json` is intentional local
state: Moto is recreated for each command, then restored from this checkpoint.

Each record has a stable `record_id` (the `uuid` field for backward compatibility) based on its source
position, and a separate deterministic SHA-256 `content_hash`. A rerun classifies records as new,
changed, or unchanged; only new and changed records are upserted. This avoids duplicate records and
unnecessary writes while still detecting content revisions. The pipeline writes CSV, Parquet, and PNG
to a temporary staging directory, atomically replaces the published artifacts only after all succeed,
then advances the checkpoint. A failure before publication leaves the last good output and checkpoint
in place; retrying converges to the same output as a clean successful run.

This demonstrates idempotent processing, content-based change detection, bounded publication
boundaries, and recovery from partial failures. It does **not** claim exactly-once delivery across a
real crawler, DynamoDB, and filesystem: production systems need durable source offsets, conditional
writes/transactions where supported, and operational reconciliation.

## Architecture

`pktscrape.sources` owns approved input adapters; `models` defines the `Experience` record;
`storage` contains the DynamoDB adapter; `exporter` writes portable files; and `analysis` builds the
small local visualization. `process/job.py` remains the optional Spark profile: it accepts either CSV
or Parquet and limits results before collecting them.

## Live collection policy

The default demo never uses a browser or network. The retained Selenium adapter is opt-in only and
has a same-host boundary, a 50-page cap, a 30-second page timeout, and explicit cleanup. Before using
it, obtain permission for the target site and review its terms, robots policy, rate limits, copyright,
and data-handling obligations. Do not use the legacy medical-review CSV as demonstration input.

## Optional AWS infrastructure

`infrastructure/` is a **non-production** Terraform example only. It creates an encrypted,
on-demand DynamoDB table and a narrowly scoped writer policy; it does not attach that policy to any
identity. Review the plan before applying:

```powershell
cd infrastructure
terraform init
terraform plan
# only after choosing an AWS account and explicit approval:
terraform apply
# remove every resource created by the stack:
terraform destroy
```

No AWS resources are created by the application, tests, or CI.

## Development

Dependencies and tool configuration are in `pyproject.toml`; CI runs Ruff and pytest on Python 3.13.
The existing `requirements.txt` is retained as an old environment snapshot, not the supported install
path.
