from fastapi import APIRouter, HTTPException, Query

from src.analysis.analytics import Analyis

router = APIRouter(prefix="/analytics", tags=["analytics"])
analysis = Analyis()


@router.get("/retrieve")
async def retrieve_data(
    norad_id: str = Query(..., description="Primary satellite NORAD identifier."),
    constellation_name: str = Query(..., description="Constellation name to analyze."),
    target_date: str | None = Query(
        None,
        description="Date in yyyy-mm-dd, mm-yyyy-dd, or dd-mm-yyyy format.",
    ),
    save_histogram: bool = Query(False, description="Save ingestion histogram to disk."),
    save_report: bool = Query(True, description="Persist the report under reports/<norad_id>_<timestamp>/."),
) -> dict[str, object]:
    try:
        return analysis.retrieve_data(
            norad_id=norad_id,
            constellation_name=constellation_name,
            target_date=target_date,
            save_histogram=save_histogram,
            save_report=save_report,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc