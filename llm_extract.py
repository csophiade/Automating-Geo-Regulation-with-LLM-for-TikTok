import json
from llm.local_llm import generate_json
# expand the schema the extractor asks for
EXTRACTOR_SYS = (
    "You are a legal text structurer. Given markdown of a law, "
    "output STRICT JSON with fields: jurisdiction, regulatory_area, law_identifiers[], and rules[]. "
    "Rules capture key obligations by article/section. Keep rule text 100–400 words."
)

def _schema_example():
    return {
      "jurisdiction": "e.g., 'EU', 'US-Federal', 'US-Utah', 'US-Florida', 'US-California'",
      "regulatory_area": "e.g., 'Child Safety', 'Transparency/DSA', 'Mandatory reporting to NCMEC'",
      "law_identifiers": [ "strings like 'DSA Art. 16', '18 U.S.C. § 2258A', 'Chapter 132 §1332B', 'Senate Hearing 137'" ],
      "rules": [
        {
          "rule_id": "string like 'DSA-Art16-1'",
          "title": "string",
          "section": "string or null",
          "chapter": "string or null",
          "article": "string or null",
          "clause": "string or null",
          "text": "string (100–400 words)",
          "keywords": ["2-8 tokens"],
          "citations": ["optional refs"]
        }
      ]
    }

def extract_struct(md_text: str) -> dict:
    user = (
        "MARKDOWN LAW TEXT:\n" + md_text[:20000] +  # safety truncation
        "\n\nReturn ONLY valid JSON with this shape (no prose):\n" +
        json.dumps(_schema_example(), indent=2)
    )
    out = generate_json(EXTRACTOR_SYS, user, temperature=0.0, max_new_tokens=1200).strip()
    if out.startswith("```"):
        out = out.strip("`")
        if "\n" in out:
            out = out.split("\n", 1)[1]
    return json.loads(out)
