import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import create_schema, retrieve_data
from config.logger import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    logging.info("CDM API server started")
    yield
    logging.info("CDM API server stopped")


app = FastAPI(
    title="CDM System API",
    version="1.0.0",
    description="Pipeline for CDM ingestion and retrieval.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(create_schema.router)
app.include_router(retrieve_data.router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
