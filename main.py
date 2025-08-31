import sys, json, os
from agents.runners import run_once, append_csv

def similar_features_by_reg(csv_path="data/outputs.csv", regs=None, top_n=5):
    if not (regs and os.path.exists(csv_path)):
        return []
    import pandas as pd
    df = pd.read_csv(csv_path)
    out = []
    for _, r in df.iterrows():
        prior_regs = set((r.get("regulations") or "").split("|"))
        if prior_regs & set(regs):
            out.append(r["feature_name"])
    return out[:top_n]

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        name = sys.argv[1]
        desc = " ".join(sys.argv[2:])
    else:
        name = "Curfew login blocker with ASL and GH for Utah minors"
        desc = "To comply with the Utah Social Media Regulation Act, we restrict logins for under-18 users at night within Utah via GH. EchoTrace logs for audits."

    res = run_once(name, desc)
    res["similar_features"] = similar_features_by_reg(regs=res["regulations"])

    def append_jsonl(row: dict, path: str = "data/audit_log.jsonl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    append_csv(res)

