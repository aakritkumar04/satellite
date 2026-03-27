import argparse
import json
import logging
import sys
import zipfile
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.config import settings
from schema.cdm import CDMRecord, create_schema as initialize_schema, get_db_session


from src.utils.util import Util


def create_schema() -> dict[str, str]:
    initialize_schema(settings.DB_URL)
    return {"status": "success", "message": "Database schema created successfully."}


class Ingestion:
    def __init__(self):
        self.util = Util()

    def ingest_all_cdms(self,zip_path: str) -> dict[str, object]:
        Session = get_db_session(settings.DB_URL)
        session = Session()
        ingested_count = 0
        batch_size = 50
        skipped_count = 0
        skipped_files: list[str] = []

        try:
            with zipfile.ZipFile(zip_path, "r") as archive:
                for filename in archive.namelist():
                    if not self.util._is_supported_cdm_entry(filename):
                        continue

                    try:
                        with archive.open(filename) as file_handle:
                            data = json.load(file_handle)
                            ingested_at = datetime.utcnow()
                            event_key = (
                                f"{data['SAT1_OBJECT_DESIGNATOR']}_"
                                f"{data['SAT2_OBJECT_DESIGNATOR']}_{data['TCA']}"
                            )

                            record = CDMRecord(
                                message_id=data["MESSAGE_ID"],
                                creation_date=datetime.fromisoformat(data["CREATION_DATE"]),
                                tca=datetime.fromisoformat(data["TCA"]),
                                sat1_id=data["SAT1_OBJECT_DESIGNATOR"],
                                sat2_id=data["SAT2_OBJECT_DESIGNATOR"],
                                constellation=data.get("CONSTELLATION", "UNKNOWN"),
                                miss_distance=float(data["MISS_DISTANCE"]),
                                event_id=event_key,
                                ingested_at=ingested_at,
                                raw_json=data,
                            )
                            session.merge(record)
                            ingested_count += 1
                            if ingested_count % batch_size == 0:
                                session.flush()
                    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                        skipped_count += 1
                        skipped_files.append(filename)
                        logging.warning("Skipping invalid CDM file %s: %s", filename, exc)

            session.commit()
            return {
                "status": "success",
                "zip_path": zip_path,
                "ingested_records": ingested_count,
                "skipped_records": skipped_count,
                "skipped_files": skipped_files,
            }
        except Exception as exc:
            session.rollback()
            logging.exception("CDM ingestion failed for %s", zip_path)
            raise exc
        finally:
            session.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create CDM schema and ingest a CDM zip archive.")
    parser.add_argument("--zip-path", required=True, help="Path to the zip archive containing CDM JSON files.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    schema_result = create_schema()
    ingestion = Ingestion()
    ingestion_result = ingestion.ingest_all_cdms(args.zip_path)
    print(json.dumps({"schema": schema_result, "ingestion": ingestion_result}, indent=2))
