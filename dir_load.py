import json, os
from typing import Dict, List, Tuple
from catalog.schema import LawArtifact

CATALOG_JSON = os.path.join(os.path.dirname(os.path.dirname(__file__)), "files", "main", "directory.json")

def _load() -> List[dict]:
    if not os.path.exists(CATALOG_JSON):
        return []
    with open(CATALOG_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def laws_by_jurisdiction() -> Dict[str, List[LawArtifact]]:
    data = _load()
    mapping: Dict[str, List[LawArtifact]] = {}
    for item in data:
        j = (item.get("jurisdiction") or "TBD").strip()
        mapping.setdefault(j, []).append(LawArtifact(**item))
    return mapping

def flat_rules_index() -> List[Tuple[str, str, str, str]]:
    """
    (jurisdiction, rule_id, title, text) for fallback searches with no jurisdiction.
    """
    out: List[Tuple[str, str, str, str]] = []
    for j, laws in laws_by_jurisdiction().items():
        for law in laws:
            for r in law.rules:
                out.append((j, r.rule_id, r.title or "", r.text or ""))
    return out
