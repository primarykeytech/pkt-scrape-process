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
`new=0 changed=0 unchanged=3 records=3`. The demo publishes a `current.json` pointer to one immutable
generation directory; Moto is recreated for each command and rehydrated from that generation's state.

Each fixture entity supplies a stable `record_id` (the `uuid` field for backward compatibility), independent
of list position, and a separate deterministic SHA-256 `content_hash`. A rerun classifies records as new,
changed, or unchanged; only new and changed records are application upserts. Moto rehydration writes are
simulation setup, not application writes. Missing IDs are retained (delta ingestion, not snapshot mirroring).
The pipeline writes CSV, Parquet, PNG, and state into an immutable generation, then atomically advances
the one `current.json` pointer. A failure before pointer publication leaves the last good generation
in place; retrying converges to the same output as a clean successful run.

This demonstrates idempotent processing, content-based change detection, bounded publication
boundaries, and recovery from partial failures. It does **not** claim exactly-once delivery across a
real crawler, DynamoDB, and filesystem: production systems need durable source offsets, conditional
writes/transactions where supported, reconciliation, and a single-writer lock or coordination policy.

## Saved raw inputs and replay

`python -m pktscrape capture-demo --raw-root artifacts/raw` saves immutable UTF-8 HTML bytes and a manifest with batch ID, stable source ID/URL, UTC capture time, SHA-256, and capture parser version. Replay it without scraping: `python -m pktscrape replay artifacts/raw/<batch-id> --output artifacts/incremental-demo`. Replay accepts the same `--rejection-threshold` option as `incremental-demo`.

Replay validates the manifest path and content hash before processing; a missing or corrupt input leaves the current published snapshot unchanged. Capture provenance remains immutable while replay records the current parser version separately. Semantic records are reproducible from retained bytes, but run timestamps and later parser changes are intentionally distinct. Retain or manually clean old batches according to your data policy; this demo never deletes them automatically.

## Data-quality gates and rejected records

The versioned `quality-v1` policy validates required fields, unique stable IDs, a documented description-length bound, and rejects an empty candidate batch. Duplicate IDs quarantine every occurrence, so an invalid first occurrence cannot make a later one appear unique. Run the default gate with `python -m pktscrape incremental-demo`; its rejection threshold is zero, so any rejected record blocks publication and preserves the current generation. A batch with zero accepted records is always fatal, even if its rejection threshold is higher. Inspect machine-readable diagnostics in `quality-failures/` for reason codes, batch rejection reason, raw-record references, accepted/rejected counts, and raw-batch provenance (source URL, byte hash, and input path). For a deliberately accepted mixed batch, use `--rejection-threshold 1`: valid records publish while rejected records remain visible in the diagnostic file. Correct the input and rerun; incremental IDs and hashes converge without duplicates.

Raw manifest/schema/hash/path failures are fatal before parsing and quarantine because their integrity cannot be trusted. This small contract makes quality decisions explicit, keeps rejected evidence visible, reconciles accepted/rejected counts, and prevents a bad batch replacing a good snapshot. It is not a complete production data-quality system; a real service also needs source-specific schema evolution and operational review.

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
