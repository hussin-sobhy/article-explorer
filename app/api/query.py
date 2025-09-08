from fastapi import APIRouter
from app.models.query import Citation, QueryRequest, QueryResponse


router= APIRouter(prefix= "/v1", tags=["query"])

@router.post("/query", response_model= QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    # pass

    return QueryResponse(
        answer= f"Dummy answer for: {request.question}",
        citations= [
            Citation(
                url="https://example.com/article",
                chunk_id="abc123",
                preview="This is a preview snippet."
            )
        ],
        latency_ms=42,
        model_version= "groq/llama-3.1-instruct",
        prompt_version="v1"
    )


