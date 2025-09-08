import httpx
from fastapi import APIRouter
from app.config import settings


router = APIRouter()


@router.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok"}


@router.get("/readyz")
def readyz():
    """Ready check endpoint"""
    try:
        resp= httpx.get(f"{settings.qdrant_url}/healthz", timeout=2.0)
        if resp.status_code == 200:
            return {"ready": True}
        return {"ready": False, "details": resp.text}

    except Exception as e:
        return {"ready": False, "error": str(e)}