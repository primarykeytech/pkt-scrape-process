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

## SQL analytics over the published snapshot

DuckDB provides a small, read-only SQL layer over the accepted `experiences.parquet` file in the one generation selected by `current.json`:

```powershell
python -m pktscrape incremental-demo --output artifacts/incremental-demo
python -m pktscrape analytics --output artifacts/incremental-demo
```

The JSON report includes `records`, distinct record IDs and content hashes, average description length, and up to 20 per-`classification` aggregates. It also returns the stored quality result and raw-replay provenance when available, plus `publication_state_filesystem_mtime_utc`: the UTC filesystem modification time of immutable `state.json`. Equivalent SQL over the loaded `experiences` relation is:

```sql
SELECT classification, count(*) AS records,
       count(DISTINCT content_hash) AS distinct_contents,
       round(avg(length(description)), 2) AS average_description_characters
FROM experiences
GROUP BY classification
ORDER BY records DESC, classification
LIMIT 20;
```

Resolving the pointer once prevents one report mixing Parquet from one generation with provenance from another. The layer is in-memory and never writes the pipeline artifacts; failed or quarantined records are absent because only an accepted published generation exports Parquet. It is intentionally a compact reporting interface, not a multi-user warehouse, semantic model, or source-freshness service: the filesystem modification time is not a publication timestamp, predates pointer publication, and can change if a generation is copied or restored. Source-capture timing is available only when replay provenance was stored.

## Optional local Dagster orchestration

The optional `dagster` extra adds the open-source Dagster OSS UI and a small asset graph. It uses no
Dagster+ account or cloud service, never crawls a live site, and reuses the existing saved-raw,
`replay_batch`, quality-gated publication, Parquet, and DuckDB functions rather than creating a second
pipeline implementation.

```powershell
python -m pip install -e ".[dev,dagster]"
$env:DAGSTER_HOME = "$PWD\.dagster"
New-Item -ItemType Directory -Force $env:DAGSTER_HOME
Copy-Item dagster.yaml.example "$env:DAGSTER_HOME\dagster.yaml"
dagster dev -m pktscrape.dagster_defs --host 127.0.0.1 --port 3000
```

Open `http://127.0.0.1:3000`, select **Materialize all**, and inspect the asset graph and run logs. The
assets are `saved_raw_batch` -> `quality_gated_publication` -> `accepted_parquet` ->
`duckdb_analytics_report`. A quality failure stops the downstream Parquet and analytics assets, while
the diagnostics written by the existing quality gate remain available. For a terminal-only safe rerun,
run the command below twice; the second replay creates a new immutable generation while reporting
unchanged accepted records rather than duplicates:

```powershell
dagster asset materialize -m pktscrape.dagster_defs --select "*"
```

`daily_offline_demo` is provided only as a visible scheduling example and starts **stopped**. Enable it
deliberately in the local UI only after choosing a single-writer policy. The asset graph uses a host-local
file lock around replay and verifies that the published generation's raw batch ID matches its upstream
asset before handing that exact generation path to Parquet and DuckDB. This prevents concurrent Dagster
runs from racing locally and prevents downstream analytics from silently resolving a newer `current.json`.
Do not run this local graph concurrently with the standalone incremental/replay CLI; the lock cannot
coordinate writers on another host.

`DAGSTER_HOME` stores local run history, event logs, and compute logs in the ignored `.dagster/` directory.
The supplied `dagster.yaml.example` sets `telemetry.enabled: false` and disables the new-user prompt for
this demo; copy it before starting the UI. Stop the local UI and daemon with `Ctrl+C`; no remote process,
schedule, or cloud resource is created. Dagster is useful here to demonstrate visible asset lineage,
failure boundaries, and local run history, but it is not a distributed scheduler, durable multi-host lock,
or production observability deployment.

## Architecture

`pktscrape.sources` owns approved input adapters; `models` defines the `Experience` record;
`storage` contains the DynamoDB adapter; `exporter` writes portable files; and `analysis` builds the
small local visualization. `sql_analytics` reads a resolved Parquet generation with DuckDB;
`dagster_defs` is the optional local asset graph. `process/job.py` remains the optional Spark profile:
it accepts either CSV or Parquet and limits results before collecting them.

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
