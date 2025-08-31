import os, json, time, csv
from typing import Dict, List, Tuple

from agents.schemas import Classification, AuditResult
from agents.prompts import (
    CLASSIFIER_PROMPT as CLASSIFIER_SYS_A,
    AUDITOR_PROMPT_STRICT as AUDITOR_SYS_STRICT,
    AUDITOR_PROMPT_RISK as AUDITOR_SYS_RISK,
)
from rag.retriever import get_retriever
from llm.local_llm import generate_json  # <-- NEW
from catalog.dir_load import laws_by_jurisdiction, flat_rules_index


by_j = laws_by_jurisdiction()
eu_laws = by_j.get("EU", [])


CLASSIFIER_SYS_B = CLASSIFIER_SYS_A + "\nAdopt a pragmatic, risk-aware interpretation when evidence is ambiguous."

def parse_json_strict(text: str) -> dict:
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if "\n" in s:
            s = s.split("\n", 1)[1]
    return json.loads(s)

def call_llm_json(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> dict:
    out = generate_json(system_prompt, user_prompt, temperature=temperature)
    try:
        return parse_json_strict(out)
    except Exception:
        fix_user = user_prompt + "\n\nYour previous output was invalid JSON. Return VALID JSON only per the schema. No prose."
        out2 = generate_json(system_prompt, fix_user, temperature=temperature)
        return parse_json_strict(out2)

def format_retrieved_chunks(resp) -> Tuple[str, List[Dict]]:
    chunks, sources = [], []
    for i, node in enumerate(resp.source_nodes):
        text = node.node.get_content(metadata_mode="none")
        meta = dict(node.node.metadata or {})
        chunks.append(f"[CTX {i+1}] {text}")
        sources.append(meta)
    return "\n\n".join(chunks), sources

def build_classifier_user(feature_text: str, retrieved_text: str) -> str:
    schema = json.dumps(Classification.model_json_schema(), indent=2)
    return (
        "FEATURE:\n" + feature_text + "\n\n"
        "RETRIEVED CONTEXT (laws/glossary/examples):\n" + retrieved_text + "\n\n"
        "Return ONLY valid JSON that matches this schema (no extra text):\n" + schema
    )

def build_auditor_user(feature_text: str, retrieved_text: str, cA: Classification, cB: Classification) -> str:
    schema = json.dumps(AuditResult.model_json_schema(), indent=2)
    return (
        "FEATURE:\n" + feature_text + "\n\n"
        "RETRIEVED CONTEXT:\n" + retrieved_text + "\n\n"
        "CLASSIFIER_A:\n" + cA.model_dump_json(indent=2) + "\n\n"
        "CLASSIFIER_B:\n" + cB.model_dump_json(indent=2) + "\n\n"
        "Return ONLY valid JSON that matches this schema (no extra text):\n" + schema
    )

def classify(feature_text: str, retrieved_text: str, system_prompt: str, temperature: float = 0.0) -> Classification:
    user = build_classifier_user(feature_text, retrieved_text)
    data = call_llm_json(system_prompt, user, temperature=temperature)
    return Classification(**data)

def audit(feature_text: str, retrieved_text: str, cA: Classification, cB: Classification, system_prompt: str) -> AuditResult:
    user = build_auditor_user(feature_text, retrieved_text, cA, cB)
    data = call_llm_json(system_prompt, user, temperature=0.0)
    return AuditResult(**data)

def run_once(feature_name: str, feature_desc: str, k: int = 5) -> dict:
    feature_text = f"{feature_name}\n{feature_desc}".strip()
    # 1) catalog context
    cat_ctx, cat_ids = _catalog_context_for_feature(feature_text, max_laws_per_j=2, max_rules_per_law=2)
    if not cat_ctx:
        cat_ctx, cat_ids = _catalog_fallback_all_rules(feature_text, top_k=4)
    
    # 2) vector RAG
    qe = get_retriever(k=k)
    resp = qe.query(feature_text)
    retrieved_text, retrieval_sources = format_retrieved_chunks(resp)
    
    # 3) combine
    combined_context = (cat_ctx + "\n\n" + retrieved_text).strip() if cat_ctx else retrieved_text

    # ---- committee (unchanged) ----
    cA = classify(feature_text, combined_context, system_prompt=CLASSIFIER_SYS_A, temperature=0.0)
    cB = classify(feature_text, combined_context, system_prompt=CLASSIFIER_SYS_B, temperature=0.3)
    aStrict = audit(feature_text, combined_context, cA, cB, system_prompt=AUDITOR_SYS_STRICT)
    aRisk   = audit(feature_text, combined_context, cA, cB, system_prompt=AUDITOR_SYS_RISK)

    both_no = (not cA.needs_geo_compliance) and (not cB.needs_geo_compliance)
    both_approve = aStrict.approve and aRisk.approve
    if both_no and both_approve:
        final = False
    else:
        yes_votes = int(cA.needs_geo_compliance) + int(cB.needs_geo_compliance)
        corrections = [x for x in (aStrict.corrected_label, aRisk.corrected_label) if x is not None]
        if len(corrections) == 2 and corrections[0] == corrections[1]:
            final = bool(corrections[0])
        else:
            final = yes_votes >= 1 or any(corrections)

    regs = sorted(set((cA.regulation_candidates or []) + (cB.regulation_candidates or [])))
    for aud in (aStrict, aRisk):
        if aud.corrected_regs:
            regs.extend(aud.corrected_regs)
    regs = sorted(set(regs))[:6]

    conf = round((cA.confidence + cB.confidence)/2.0, 3)
    if both_no and both_approve:
        conf = max(conf, 0.85)

    result = {
        "feature_name": feature_name,
        "needs_geo_compliance": final,
        "confidence": conf,
        "regulations": regs,
        "catalog_rule_ids": cat_ids,             
        "classifier_A": cA.model_dump(),
        "classifier_B": cB.model_dump(),
        "auditor_strict": aStrict.model_dump(),
        "auditor_risk": aRisk.model_dump(),
        "retrieval_sources": retrieval_sources,
        "timestamp": time.time(),
        "catalog_rule_ids": "|".join(row.get("catalog_rule_ids", [])),
        "models": {
            "voter_A": os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
            "voter_B": os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
            "auditors": [
                os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
                os.environ.get("LLM_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
            ],
        },
        "embeddings": "BAAI/bge-small-en-v1.5",
    }
    return result

def append_csv(row: dict, csv_path: str = "data/outputs.csv"):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    headers = [
        "feature_name", "needs_geo_compliance", "confidence",
        "regulations", "classifier_A", "classifier_B",
        "auditor_strict", "auditor_risk", "retrieval_sources",
        "timestamp", "models", "embeddings"
    ]
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        if not exists:
            w.writeheader()
        w.writerow({
            "feature_name": row["feature_name"],
            "needs_geo_compliance": row["needs_geo_compliance"],
            "confidence": row["confidence"],
            "catalog_rule_ids": "|".join(row.get("catalog_rule_ids", [])),
            "regulations": "|".join(row["regulations"]),
            "classifier_A": json.dumps(row["classifier_A"], ensure_ascii=False),
            "classifier_B": json.dumps(row["classifier_B"], ensure_ascii=False),
            "auditor_strict": json.dumps(row["auditor_strict"], ensure_ascii=False),
            "auditor_risk": json.dumps(row["auditor_risk"], ensure_ascii=False),
            "retrieval_sources": json.dumps(row["retrieval_sources"], ensure_ascii=False),
            "timestamp": row["timestamp"],
            "models": json.dumps(row["models"], ensure_ascii=False),
            "embeddings": row["embeddings"],
        })

from catalog.dir_load import laws_by_jurisdiction, flat_rules_index

def _guess_jurisdictions(text: str) -> list[str]:
    t = text.lower()
    js = []
    if any(k in t for k in ["eea", "eu", "european union", "europe"]): js.append("EU")
    if "utah" in t: js.append("US-Utah")
    if "florida" in t: js.append("US-Florida")
    if "california" in t or " ca " in t: js.append("US-California")
    if any(k in t for k in ["ncmec", "federal", "18 u.s.c", "us code", "us federal"]): js.append("US-Federal")
    return list(dict.fromkeys(js))

def _catalog_context_for_feature(feature_text: str, max_laws_per_j=2, max_rules_per_law=2) -> tuple[str, list[str]]:
    by_j = laws_by_jurisdiction()
    wants = _guess_jurisdictions(feature_text)
    parts, used_ids = [], []
    for j in wants:
        for law in by_j.get(j, [])[:max_laws_per_j]:
            for r in law.rules[:max_rules_per_law]:
                parts.append(f"[CAT {j} {r.rule_id}] {r.title} — {r.text}")
                used_ids.append(f"{j}:{r.rule_id}")
    return ("\n\n".join(parts), used_ids)

def _catalog_fallback_all_rules(feature_text: str, top_k: int = 4) -> tuple[str, list[str]]:
    feats = set(w.strip(",.:;()[]").lower() for w in feature_text.split() if len(w) > 3)
    scored = []
    for j, rid, title, text in flat_rules_index():
        kw = set(title.lower().split())
        score = len(kw & feats)
        if score:
            scored.append((score, j, rid, title, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    parts, used_ids = [], []
    for _, j, rid, title, text in scored[:top_k]:
        parts.append(f"[CAT {j} {rid}] {title} — {text}")
        used_ids.append(f"{j}:{rid}")
    return ("\n\n".join(parts), used_ids)
