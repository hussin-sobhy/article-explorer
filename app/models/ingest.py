from pydantic import BaseModel, HttpUrl, Field, constr, conint
from typing import List, Optional, Dict

class IngestRequest(BaseModel):
    urls: List[HttpUrl] = Field(..., min_items=1, description="At least one URL required.")
    source_tag: Optional[constr(strip_whitespace=True, min_length=1, max_length=32)] = Field(
        None, description="Logical corpus label (e.g., 'demo', 'docs')."
    )



class IngestResponse(BaseModel):
    accepted: conint(ge=0)
    failed: List[str] = Field(default_factory=list)
    summary: Dict[str, str] = Field(default_factory=dict)




