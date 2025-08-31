from pydantic import BaseModel, Field
from typing import List, Optional

class Classification(BaseModel):
    needs_geo_compliance: bool
    confidence: float = Field(ge=0, le=1)
    regulation_candidates: List[str]
    reasoning: str

class AuditResult(BaseModel):
    approve: bool
    corrected_label: Optional[bool] = None
    corrected_regs: Optional[List[str]] = None
    fixes: Optional[str] = None