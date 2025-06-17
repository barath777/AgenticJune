import pandas as pd
import numpy as np
import faiss
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer

class EmbeddingStore:
    def __init__(self, csv_path, model_name="all-MiniLM-L6-v2", output_dir="storage"):
        self.base_dir = Path(__file__).resolve().parent
        self.csv_path = self.base_dir.parent / csv_path  # Data/Historical_Alerts_Resolutions.csv
        self.output_dir = self.base_dir / output_dir 
        self.model_name = model_name

        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_index_path = self.output_dir / "faiss_index.bin"
        self.processed_data_path = self.output_dir / "processed_alerts.csv"

        
        self.df = None
        self.model = SentenceTransformer(self.model_name)
        self.index = None
    
    #Load and prepare data for embedding
    def load_and_preprocess_data(self):
        try:
            self.df = pd.read_csv(self.csv_path)
            self.df.fillna("", inplace=True)
            self.df["alert_timestamp"] = self.df["alert_timestamp"].astype(str)
            self.df["text"] = (
                self.df["alert_timestamp"] + " " + self.df["alert_type"] + " " + 
                self.df["resolution_steps"] + " " + self.df["application"] + " " + 
                self.df["severity"] + " " + self.df["root_cause"] + " " + 
                self.df["change_implemented"] + " " + self.df["post_resolution_status"]
            )
        except Exception as e:
            print(f"Data loading failed: {str(e)}")
            raise
    
    #Generate embeddings from processed text
    def create_embeddings(self):
        if self.df is None or "text" not in self.df.columns:
            raise ValueError("Data not properly loaded")
            
        embeddings = self.model.encode(self.df["text"].tolist(), show_progress_bar=True)
        embeddings_array = np.array(embeddings).astype("float32")
        return embeddings_array / np.linalg.norm(embeddings_array, axis=1, keepdims=True)
    
    #Create and save FAISS index
    def store_in_faiss(self, embeddings_array):
        try:
            dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings_array)
            faiss.write_index(self.index, str(self.faiss_index_path))
        except Exception as e:
            print(f"FAISS storage failed: {str(e)}")
            raise
    
    #Save processed CSV
    def save_processed_data(self):
        try:
            self.df.to_csv(self.processed_data_path, index=False)
        except Exception as e:
            print(f"Failed to save processed data: {str(e)}")
            raise
    
    #Load pre-created artifacts
    def load(self):
        self.index = faiss.read_index(str(self.faiss_index_path))
        self.df = pd.read_csv(self.processed_data_path)
        return self
    
    #Complete pipeline execution
    def run(self):
        print("Starting embedding pipeline...")
        self.load_and_preprocess_data()
        embeddings = self.create_embeddings()
        self.store_in_faiss(embeddings)
        self.save_processed_data()
        print("Embeddings stored successfully in:", self.output_dir)

if __name__ == "__main__":
    store = EmbeddingStore("Data/Historical_Alerts_Resolutions.csv")
    store.run()