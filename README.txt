python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
    
    Build/refresh the catalog (PDF→MD if missing, HF extraction, JSON upsert)
python -m tools.update_cat

    (Optional) rebuild RAG so retriever sees latest MDs
python rag/ingest.py

    Single feature → JSON/CSV/JSONL with traceability
python main.py "Feature name" "Feature description"

    Batch
python evaluation/run_batch.py


Frontend: Streamlit (demo UI)
Backend: Python + LlamaIndex (RAG)
Models: HuggingFace (BAAI/bge embeddings, Qwen/Phi for LLM)
Storage: FAISS/Chroma VectorDB, JSON catalog, CSV logs
Tools: MarkItDown for PDF→MD, Pydantic schemas, pandas
