from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import StorageContext
import os

LAW_DIR = "files/laws/md"
MAIN_DIR = "files/main"
PERSIST_DIR = "rag_index"

def build_index():
    # Load documents (regulations + glossary)
    docs_law = SimpleDirectoryReader(LAW_DIR).load_data()          
    docs_main = SimpleDirectoryReader(MAIN_DIR).load_data()        
    docs = docs_law + docs_main                                    

    splitter = SentenceSplitter(chunk_size=800, chunk_overlap=100)
    embed = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    index = VectorStoreIndex.from_documents(docs, transformations=[splitter], embed_model=embed)
    os.makedirs(PERSIST_DIR, exist_ok=True)
    index.storage_context.persist(persist_dir=PERSIST_DIR)

if __name__ == "__main__":
    build_index()