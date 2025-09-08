from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.ingest import router as ingest_router
from app.api.query import router as query_router

app = FastAPI(title= "Article Explorer API")

app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(query_router)