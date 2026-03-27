import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.util import Util

import matplotlib.pyplot as plt
from sqlalchemy import func

from config.config import settings
from schema.cdm import CDMRecord, get_db_session

TARGET_DATE = datetime(2025, 10, 22)


class Analyis:
    def __init__(self):
        self.util = Util()
        self.report = Report(analysis=self)

    def retrieve_data(
        self,
        norad_id: str,
        constellation_name: str,
        target_date: str | datetime | None = TARGET_DATE,
        save_histogram: bool = False,
        save_report: bool = True,
    ) -> dict[str, object]:
        Session = get_db_session(settings.DB_URL)
        session = Session()
        normalized_target_date = self.util._normalize_target_date(target_date)

        try:
            future_cdms = session.query(CDMRecord).filter(
                CDMRecord.sat1_id == norad_id,
                CDMRecord.tca > normalized_target_date,
            ).all()
            smallest_miss_distance = session.query(func.min(CDMRecord.miss_distance)).filter(
                CDMRecord.constellation == constellation_name,
                CDMRecord.tca > normalized_target_date,
            ).scalar()
            distinct_events = session.query(func.count(func.distinct(CDMRecord.event_id))).scalar() or 0
            total_cdms = session.query(func.count(CDMRecord.id)).scalar() or 0
            avg_cdms = total_cdms / distinct_events if distinct_events > 0 else 0
            hourly_ingestion_counts = self.report.get_hourly_ingestion_counts(session)
            report = {
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "target_date": normalized_target_date.isoformat(),
                "norad_id": norad_id,
                "constellation_name": constellation_name,
                "future_cdms": [
                    {
                        "message_id": record.message_id,
                        "tca": record.tca.isoformat(),
                        "sat1_id": record.sat1_id,
                        "sat2_id": record.sat2_id,
                        "miss_distance": record.miss_distance,
                    }
                    for record in future_cdms
                ],
                "smallest_miss_distance": smallest_miss_distance,
                "hourly_ingestion_counts": hourly_ingestion_counts,
                "distinct_conjunction_events": distinct_events,
                "average_cdms_per_event": round(avg_cdms, 2),
                "histogram_path": None,
            }
            report_directory = None
            if save_report:
                report_directory = self.report.save_report_artifacts(
                    norad_id=norad_id,
                    report=report,
                    save_histogram=save_histogram,
                )
                report["report_directory"] = report_directory
                if save_histogram:
                    report["histogram_path"] = str(Path(report_directory) / "ingestion_histogram.png")
            elif save_histogram:
                report["histogram_path"] = self.report.generate_histogram(hourly_ingestion_counts)

            return report
        finally:
            session.close()


class Report:
    def __init__(self,analysis=None):
        self.analysis = analysis

    def get_hourly_ingestion_counts(self,session) -> dict[str, int]:
        ingestion_times = session.query(CDMRecord.ingested_at).all()
        hourly_counts = {f"{hour:02d}:00": 0 for hour in range(24)}
        for timestamp in ingestion_times:
            hourly_counts[f"{timestamp[0].hour:02d}:00"] += 1
        return hourly_counts


    def generate_histogram(self,hourly_ingestion_counts: dict[str, int]) -> str:
        return self.generate_histogram_to_path(hourly_ingestion_counts, "ingestion_histogram.png")


    def generate_histogram_to_path(self,hourly_ingestion_counts: dict[str, int], output_path: str) -> str:
        hours = [int(hour.split(":")[0]) for hour in hourly_ingestion_counts.keys()]
        counts = list(hourly_ingestion_counts.values())

        plt.figure(figsize=(10, 6))
        plt.bar(hours, counts, color="skyblue", edgecolor="black", alpha=0.7)
        plt.title("CDM Database Ingestion Frequency (By Hour)")
        plt.xlabel("Hour of Day (UTC)")
        plt.ylabel("Number of CDMs Ingested")
        plt.xticks(range(0, 24))
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        plt.savefig(output_path)
        plt.close()
        return output_path


    def save_report_artifacts(
        self,
        norad_id: str,
        report: dict[str, object],
        save_histogram: bool,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_directory = Path("reports") / f"{norad_id}_{timestamp}"
        report_directory.mkdir(parents=True, exist_ok=True)

        report_path = report_directory / "report.json"
        report_payload = dict(report)

        if save_histogram:
            histogram_path = report_directory / "ingestion_histogram.png"
            self.generate_histogram_to_path(report["hourly_ingestion_counts"], str(histogram_path))
            report_payload["histogram_path"] = str(histogram_path)

        report_payload["report_directory"] = str(report_directory)
        report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        return str(report_directory)


    def generate_report(
        self,
        norad_id: str,
        constellation_name: str,
        target_date: str | datetime | None = TARGET_DATE,
        save_histogram: bool = True,
        save_report: bool = True,
    ):
        report = self.analysis.retrieve_data(
            norad_id=norad_id,
            constellation_name=constellation_name,
            target_date=target_date,
            save_histogram=save_histogram,
            save_report=save_report,
        )
        print(f"--- KAYHAN SPACE ANALYTICS REPORT ({report['report_date']}) ---")
        print(
            f"\n[1] CDMs for NORAD ID {norad_id} "
            f"(TCA after {datetime.fromisoformat(report['target_date']).date()}):"
        )
        for record in report["future_cdms"]:
            print(f"    - Message ID: {record['message_id']} | TCA: {record['tca']}")
        print(
            f"\n[2] Smallest Miss Distance for Constellation '{constellation_name}': "
            f"{report['smallest_miss_distance'] or 'N/A'} m"
        )
        print("\n[3] Number of CDMs ingested, windowed by hour:")
        for hour, count in report["hourly_ingestion_counts"].items():
            print(f"    - {hour}: {count}")
        print(f"\n[4] Total Distinct Conjunction Events: {report['distinct_conjunction_events']}")
        print(f"\n[5] Average CDMs per Event: {report['average_cdms_per_event']:.2f}")
        print(f"\n[6] Ingestion histogram saved as '{report['histogram_path']}'")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a CDM analytics report.")
    parser.add_argument("--norad-id", required=True, help="Primary object designator / NORAD ID.")
    parser.add_argument("--constellation-name", required=True, help="Constellation name to query.")
    parser.add_argument(
        "--target-date",
        default=None,
        help="Date in yyyy-mm-dd, mm-yyyy-dd, or dd-mm-yyyy format.",
    )
    parser.add_argument(
        "--save-histogram",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save the ingestion histogram image.",
    )
    parser.add_argument(
        "--save-report",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Save report artifacts under reports/<norad_id>_<timestamp>/.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    analysis = Analyis()
    analysis.report.generate_report(
        norad_id=args.norad_id,
        constellation_name=args.constellation_name,
        target_date=args.target_date,
        save_histogram=args.save_histogram,
        save_report=args.save_report,
    )
