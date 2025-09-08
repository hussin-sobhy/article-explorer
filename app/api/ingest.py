from fastapi import APIRouter
from app.models.ingest import IngestRequest, IngestResponse
from app.config import settings

router = APIRouter(prefix= "/v1", tags= ["ingest"])

@router.post("/ingest", response_model= IngestResponse)
async def ingest(request: IngestRequest) -> IngestResponse:

    # pass
    return IngestResponse(
        accepted= len(request.urls), 
        failed= [], 
        summary= {
            "total_chunks": "0", 
            "embedding_model": "sentence-transformers/all-mpnet-base-v2"
        }
    )

