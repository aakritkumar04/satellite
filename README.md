# CDM System

This project exposes a small FastAPI service for:

- creating the CDM database schema
- ingesting CDMs from a zip archive of JSON files
- generating analytics reports for ingested CDMs
- saving each generated report under `reports/<norad_id>_<timestamp>/`

## Run The API

Run from the repository root:

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Environment

The API reads database settings from:

[`.env`](/Users/aakritkumar/Desktop/round/CDM_system/.env)

Current required variable:

```env
DB_URL=postgresql://user:password@localhost:5432/db_name
```

The database credentials must be valid before `/schema/create` or `/analytics/retrieve` will work.

## Run From CLI

You can also run ingestion and analytics directly from the command line.

### Ingest CDMs From A Zip

This creates the schema first and then ingests the provided zip archive.

```bash
python3 CDM_system/src/etl/ingest.py --zip-path /Users/aakritkumar/Desktop/round/cdm_archive.zip
```

Help:

```bash
python3 CDM_system/src/etl/ingest.py --help
```

### Generate Analytics Report

This takes arguments from the user and can save both the JSON report and histogram.

```bash
python3 CDM_system/src/analysis/analytics.py \
  --norad-id 100000 \
  --constellation-name ORION \
  --target-date 2025-10-22 \
  --save-histogram \
  --save-report
```

Optional flags:

- `--target-date` accepts `yyyy-mm-dd`, `mm-yyyy-dd`, or `dd-mm-yyyy`
- `--no-save-histogram` disables histogram output
- `--no-save-report` disables report folder creation

Help:

```bash
python3 CDM_system/src/analysis/analytics.py --help
```

## APIs

### 1. Create Schema

Endpoint:

```text
POST /schema/create
```

Purpose:

- create the database schema
- optionally ingest CDMs immediately after schema creation

Request body:

```json
{
  "zip_path": "path/to/cdms.zip",
  "ingest_data": true
}
```

Fields:

- `zip_path`: path to a zip archive containing JSON CDM files
- `ingest_data`: if `true`, the API will ingest the zip after creating the schema

Example:

```bash
curl -X POST http://127.0.0.1:8000/schema/create \
  -H "Content-Type: application/json" \
  -d '{
    "zip_path": "sample_cdms.zip",
    "ingest_data": true
  }'
```

Example response:

```json
{
  "schema": {
    "status": "success",
    "message": "Database schema created successfully."
  },
  "ingestion": {
    "status": "success",
    "zip_path": "sample_cdms.zip",
    "ingested_records": 42
  }
}
```

Important:

- this endpoint currently expects a zip file
- it does not currently ingest the extracted `cdm_archive/` directory directly

### 2. Retrieve Analytics Report

Endpoint:

```text
GET /analytics/retrieve
```

This endpoint uses query parameters.

Purpose:

- query all CDMs for a NORAD ID whose `TCA` is after a user-supplied date
- compute the smallest miss distance for a constellation after that date
- compute hourly ingestion counts based on `ingested_at`
- compute distinct conjunction event count
- compute average CDMs per distinct conjunction event
- optionally save histogram and report artifacts

Query parameters:

- `norad_id` required
- `constellation_name` required
- `target_date` optional
- `save_histogram` optional, default `false`
- `save_report` optional, default `true`

Postman setup:

- Method: `GET`
- URL: `http://127.0.0.1:8000/analytics/retrieve`
- Params tab:
- `norad_id` = `100000`
- `constellation_name` = `ORION`
- `target_date` = `2025-10-22`
- `save_histogram` = `true`
- `save_report` = `true`

Equivalent URL:

```text
http://127.0.0.1:8000/analytics/retrieve?norad_id=100000&constellation_name=ORION&target_date=2025-10-22&save_histogram=true&save_report=true
```

Accepted `target_date` formats:

- `yyyy-mm-dd`
- `mm-yyyy-dd`
- `dd-mm-yyyy`

Examples that normalize to the same date:

- `2025-10-22`
- `10-2025-22`
- `22-10-2025`

Example:

```bash
curl "http://127.0.0.1:8000/analytics/retrieve?norad_id=100000&constellation_name=ORION&target_date=2025-10-22&save_histogram=true&save_report=true"
```

Example response:

```json
{
  "report_date": "2026-03-25",
  "target_date": "2025-10-22T00:00:00",
  "norad_id": "100000",
  "constellation_name": "ORION",
  "future_cdms": [],
  "smallest_miss_distance": null,
  "hourly_ingestion_counts": {
    "00:00": 0,
    "01:00": 0,
    "02:00": 0
  },
  "distinct_conjunction_events": 0,
  "average_cdms_per_event": 0.0,
  "histogram_path": "reports/100000_20260325_223106/ingestion_histogram.png",
  "report_directory": "reports/100000_20260325_223106"
}
```

## Saved Reports

When `save_report=true`, the API writes report artifacts to:

```text
reports/<norad_id>_<timestamp>/
```

Contents:

- `report.json`
- `ingestion_histogram.png` if `save_histogram=true`

Example:

```text
reports/100000_20260325_223106/
```

## What The Report Covers

The analytics endpoint supports these requested outputs:

- all CDMs for a given primary by object designator whose `TCA` is in the future relative to the supplied date
- smallest miss distance for a given constellation for CDMs whose `TCA` is in the future relative to the supplied date
- number of CDMs ingested, windowed by hour
- histogram image of hourly ingestion counts
- number of distinct conjunction events
- average number of CDMs per distinct conjunction event

## Notes And Current Limitations

- The ingestion endpoint currently expects a zip archive, not a directory of extracted JSON files.
- The report histogram is based on the database ingestion timestamp `ingested_at`.
- If the table already existed before `ingested_at` was added, you may need to recreate the table or run a migration.
- If Postgres rejects the credentials in `CDM_system/.env`, the API starts but DB-backed routes fail at runtime.
