from llama_index.core import load_index_from_storage, StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

def get_retriever(persist_dir="rag_index", k=5):
    storage = StorageContext.from_defaults(persist_dir=persist_dir)
    embed = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    index = load_index_from_storage(storage, embed_model=embed)
    # response_mode="no_text" returns sources which is good for RAG grounding
    return index.as_query_engine(similarity_top_k=k, response_mode="no_text")

def format_sources(resp):
    texts, metas = [], []
    for i, sn in enumerate(resp.source_nodes):
        texts.append(f"[CTX {i+1}] " + sn.node.get_content(metadata_mode="none"))
        metas.append(dict(sn.node.metadata or {}))
    return "\n\n".join(texts), metas