from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.etl.ingest import create_schema as create_schema_service
from src.etl.ingest import Ingestion

router = APIRouter(prefix="/schema", tags=["schema"])
ingest = Ingestion()

class CreateSchemaRequest(BaseModel):
    zip_path: str | None = None
    ingest_data: bool = False


@router.post("/create")
async def create_schema(request: CreateSchemaRequest) -> dict[str, object]:
    try:
        result: dict[str, object] = {"schema": create_schema_service()}

        if request.ingest_data:
            if not request.zip_path:
                raise HTTPException(status_code=400, detail="zip_path is required when ingest_data is true.")
            result["ingestion"] = ingest.ingest_all_cdms(request.zip_path)

        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
