import os, json, hashlib
from typing import List, Dict, Optional
from markitdown import MarkItDown
from catalog.llm_extract import extract_struct

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
PDF_DIR = os.path.join(PROJECT_ROOT, "files", "laws")
MD_DIR = os.path.join(PDF_DIR, "md")
CATALOG_JSON = os.path.join(PROJECT_ROOT, "files", "main", "directory.json")


FAST_MODE = os.getenv("FAST_MODE", "1") == "1"  


def _read_json(path: str) -> Optional[List[Dict]]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def _write_json(path: str, data: List[Dict]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def _upsert(catalog: List[Dict], item: Dict) -> List[Dict]:
    by_key = { (c.get("md_file") or c.get("filename")): c for c in catalog }
    key = item.get("md_file") or item.get("filename")
    by_key[key] = item
    return list(by_key.values())


def _ensure_md_from_pdfs() -> List[str]:
    """
    Ensure each PDF has a corresponding .md.
    Convert PDF→MD only if the .md doesn't exist.
    Return a list of absolute md file paths to process.
    """
    os.makedirs(MD_DIR, exist_ok=True)
    md = MarkItDown()
    md_paths: List[str] = []

    for filename in os.listdir(PDF_DIR):
        if not filename.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(PDF_DIR, filename)
        base = os.path.splitext(filename)[0]
        md_path = os.path.join(MD_DIR, base + ".md")

        if not os.path.exists(md_path):
            try:
                res = md.convert(pdf_path)
                with open(md_path, "w", encoding="utf-8") as f:
                    f.write(res.text_content)
                print(f"PDF→MD: created {os.path.basename(md_path)}")
            except Exception as e:
                print(f"X PDF→MD failed on {filename}: {e}")
                continue
        else:
            print(f"skip (MD exists): {os.path.basename(md_path)}")

        md_paths.append(md_path)

    # Also include any stray MDs that exist without a matching PDF (optional)
    for md_name in os.listdir(MD_DIR):
        if md_name.lower().endswith(".md"):
            full = os.path.join(MD_DIR, md_name)
            if full not in md_paths:
                md_paths.append(full)

    return sorted(md_paths)

def _md_is_in_catalog(catalog, md_name: str) -> bool:
    return any((c.get("md_file","").endswith(md_name)) for c in catalog)

def update_catalog():
    md_paths = _ensure_md_from_pdfs()
    catalog = _read_json(CATALOG_JSON) or []
    updated = catalog[:]

    for md_path in md_paths:
        md_name = os.path.basename(md_path)
        base = os.path.splitext(md_name)[0]
        pdf_guess = base + ".pdf"
        print(f"→ extracting from {md_name}")

        if FAST_MODE and _md_is_in_catalog(catalog, md_name):
            print("   fast mode: already in catalog, skipping extraction")
            continue

        # 1. read md text
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()
        except Exception as e:
            print(f"X read failed: {e}")
            continue

        # 2. run extraction (jurisdiction, rules, etc.)
        try:
            struct = extract_struct(md_text)
        except Exception as e:
            print(f"X LLM extract failed: {e}")
            struct = {"jurisdiction": "TBD", "regulatory_area": "TBD", "rules": []}

        # 3. build artifact
        art = {
            "filename": pdf_guess,
            "original_file": f"files/laws/{pdf_guess}",
            "md_file": f"files/laws/md/{md_name}",
            "title": base.replace("_", " "),
            "regulatory_area": struct.get("regulatory_area", "TBD"),
            "jurisdiction": struct.get("jurisdiction", "TBD"),
            "rules": [],
        }

        rules = []
        for i, r in enumerate(struct.get("rules", []), 1):
            rid = r.get("rule_id") or f"{base}-R{i}"
            rules.append({
                "rule_id": rid,
                "title": r.get("title", f"Rule {i}"),
                "section": r.get("section"),
                "text": (r.get("text") or "")[:4000],
                "keywords": r.get("keywords", []),
                "citations": r.get("citations", []),
            })
        art["rules"] = rules

        # 4. merge into catalog
        updated = _upsert(updated, art)
        print(f"added {md_name} ({len(rules)} rules)")

    # 5. write to disk
    _write_json(CATALOG_JSON, updated)
    print("saved")


if __name__ == "__main__":
    # If you run directly (not via `python -m`), ensure project root is on sys.path if needed:
    # import sys
    # sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    update_catalog()