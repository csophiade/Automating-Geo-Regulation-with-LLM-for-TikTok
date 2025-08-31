
from typing import List, Optional, Dict
from pydantic import BaseModel

class Rule(BaseModel):
    rule_id: str
    title: str
    section: Optional[str] = None
    text: str
    keywords: List[str] = []
    citations: List[str] = []

class LawArtifact(BaseModel):
    filename: str
    original_file: str
    md_file: str
    title: str
    regulatory_area: str
    jurisdiction: str
    law_identifiers: List[str] = []        # NEW e.g. "DSA Art. 16", "18 U.S.C. § 2258A"
    rules: List[Rule] = []