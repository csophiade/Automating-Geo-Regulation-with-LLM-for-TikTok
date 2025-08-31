Automating Geo-Regulation Compliance with LLMs
Problem Statement

TikTok operates across multiple jurisdictions, where each new feature must comply with region-specific regulations such as GDPR (EU), SB976 (California), Utah’s Social Media Regulation Act, Florida child protection laws, and U.S. federal reporting requirements.

Manual compliance review is slow, reactive, and prone to oversight. This project develops a prototype system to:

Flag features that require geo-specific compliance logic

Provide reasoning and cite relevant regulations

Generate an auditable evidence trail for regulatory inquiries

The objective is to reduce compliance governance costs, minimize risk exposure, and establish traceability before features are launched.

Approach

1. Document Ingestion

PDFs converted to Markdown with MarkItDown

Catalog builder extracts: jurisdiction, regulatory area, rule identifiers (sections, articles, statutes)

Stored in files/main/directory.json

2. Retrieval-Augmented Generation (RAG)

FAISS/Chroma vector store for law snippets and glossary

Embeddings: BAAI/bge-small-en-v1.5 for semantic recall

LlamaIndex query engine for top-k retrieval

3. Classification and Audit

Committee of agents:

Two classifiers (different prompts/temperatures)

Two auditors (strict textualist vs. risk-oriented)

Consensus rules reduce false negatives and enforce conservative bias

4. Outputs

JSON/CSV logs with compliance decision, reasoning, regulation references, and retrieval sources

Designed for auditability and traceability

Advantages

Hybrid retrieval: semantic search plus structured jurisdictional catalog

Committee approach: mitigates bias and hallucination of a single model

Built-in traceability: every output cites underlying laws and rules

Modular design: supports HuggingFace, OpenAI, or TikTok’s internal models

Usage

Setup

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Build/refresh catalog
Converts PDFs to Markdown, extracts rules, and updates directory.json:

python -m tools.update_cat


Rebuild RAG index (optional)

python rag/ingest.py


Single feature classification

python main.py "Feature name" "Feature description"


Batch classification

python evaluation/run_batch.py

Stack

Frontend: Streamlit (demo UI)

Backend: Python, LlamaIndex

Models: HuggingFace (BAAI/bge embeddings, Qwen/Phi LLMs)

Storage: FAISS/Chroma VectorDB, JSON catalog, CSV logs

Tools: MarkItDown, Pydantic, pandas

Future Work

Broaden coverage with additional jurisdictions (e.g., Brazil LGPD, India DPDP Act)

Add flat global rule index for features with no jurisdiction specified

Detect overlap between features with similar compliance obligations

Experiment with TikTok’s seedream LLM for domain-specific classification

Integrate into CI/CD for automated compliance screening on new feature rollouts

Outputs

files/main/directory.json — structured catalog of laws and rules

rag_index/ — vector embeddings for retrieval

data/outputs.csv — compliance decisions and audit trail