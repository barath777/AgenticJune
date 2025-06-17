import os
import faiss
import pickle
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer


# INDEX_DIR = "faiss_index"
BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "faiss_index"
top_k = 3  # Number of top similar SOPs to return

def load_faiss_index(index_dir: str):
    index = faiss.read_index(f"{INDEX_DIR}/sop.index")
    with open(f"{INDEX_DIR}/entries.pkl", "rb") as f:
        sop_entries = pickle.load(f)
    return index, sop_entries

def embed_query(query: str, model: SentenceTransformer):
    return model.encode([query])

def search_sop(query: str):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    index, sop_entries = load_faiss_index(INDEX_DIR)
    query_vector = embed_query(query, model)
    distances, indices = index.search(np.array(query_vector), top_k)
    
    results = []
    for i in indices[0]:
        if i < len(sop_entries):
            results.append(sop_entries[i])
    return results