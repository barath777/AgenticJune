import os
import json
import pickle
import faiss
from typing import List
from sentence_transformers import SentenceTransformer
import numpy as np

SOP_JSONL_PATH = "sop_docs/sop_master.jsonl"
INDEX_DIR = "faiss_index"

def load_sop_data(jsonl_path: str) -> List[dict]:
    sop_entries = []
    with open(jsonl_path, "r") as file:
        for line in file:
            sop = json.loads(line)
            sop_entries.append(sop)
    return sop_entries

def prepare_texts_for_embedding(sop_entries: List[dict]) -> List[str]:
    return [
        f"{entry['title']} - {entry['description']} - {' '.join(entry['resolution_steps'])}"
        for entry in sop_entries
    ]

def create_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatL2:
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)
    return index

def save_index(index: faiss.IndexFlatL2, sop_entries: List[dict], directory: str):
    os.makedirs(directory, exist_ok=True)
    faiss.write_index(index, os.path.join(directory, "sop.index"))
    with open(os.path.join(directory, "entries.pkl"), "wb") as f:
        pickle.dump(sop_entries, f)
    print(f"FAISS index and SOP metadata saved to '{directory}'")

def main():
    print("Loading SOP entries...")
    sop_entries = load_sop_data(SOP_JSONL_PATH)

    print("Generating embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = prepare_texts_for_embedding(sop_entries)
    embeddings = model.encode(texts)

    print("Creating FAISS index...")
    index = create_faiss_index(embeddings)

    print("Saving index and metadata...")
    save_index(index, sop_entries, INDEX_DIR)

    print("✅ FAISS index creation completed.")

if __name__ == "__main__":
    main()
