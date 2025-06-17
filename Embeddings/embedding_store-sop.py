import os
import json
import faiss
import pickle
from typing import List, Dict
from sentence_transformers import SentenceTransformer

class SOPStore:
    def __init__(self, sop_path="sop_master.jsonl", index_path="faiss_index"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.sop_path = sop_path
        self.index_path = index_path
        self.sop_entries: List[Dict] = []  # Each is full SOP dict
        self.index = None
        self.load_or_create_index()

    def load_or_create_index(self):
        if os.path.exists(os.path.join(self.index_path, "sop.index")):
            with open(os.path.join(self.index_path, "entries.pkl"), "rb") as f:
                self.sop_entries = pickle.load(f)
            self.index = faiss.read_index(os.path.join(self.index_path, "sop.index"))
        else:
            with open(self.sop_path, "r") as f:
                for line in f:
                    sop = json.loads(line)
                    self.sop_entries.append(sop)

            # Create embedding from concatenated relevant fields
            texts = [
                f"{entry['title']}\n{entry['description']}\n{' '.join(entry['resolution_steps'])}"
                for entry in self.sop_entries
            ]
            embeddings = self.model.encode(texts)

            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)

            os.makedirs(self.index_path, exist_ok=True)
            faiss.write_index(self.index, os.path.join(self.index_path, "sop.index"))
            with open(os.path.join(self.index_path, "entries.pkl"), "wb") as f:
                pickle.dump(self.sop_entries, f)

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        query_vec = self.model.encode([query])
        D, I = self.index.search(query_vec, top_k)
        return [self.sop_entries[i] for i in I[0]]


if __name__ == "__main__":
    store = SOPStore("sop_master.jsonl")
    store.load_or_create_index()