from pydantic import BaseModel, constr, conint, Field, HttpUrl
from typing import List, Optional

class QueryRequest(BaseModel):
    question: constr(strip_whitespace=True, min_length=5)  # reduce low-signal queries
    top_k: conint(ge=1, le=20) = 5                         # guard latency/cost
    source_filter: Optional[List[constr(strip_whitespace=True, min_length=1, max_length=32)]] = None



class Citation(BaseModel):
    url: HttpUrl
    chunk_id: constr(strip_whitespace=True, min_length=1, max_length=64)
    preview: constr(strip_whitespace=True, min_length=1, max_length=240)

class QueryResponse(BaseModel):
    answer: constr(min_length=1)
    citations: List[Citation] = Field(default_factory=list)
    latency_ms: conint(ge=0)
    model_version: constr(min_length=1)
    prompt_version: constr(min_length=1)



