import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class KnowledgeBase:
    def __init__(self, folder="knowledge_base"):
        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )
        self.documents = []
        self.index = None

        if not os.path.isdir(folder):
            print(f"Warning: knowledge base folder '{folder}' not found. "
                  "The agent will run without retrieval context.")
            return

        for filename in os.listdir(folder):
            path = os.path.join(folder, filename)
            if filename.endswith(".txt"):
                with open(path, "r", encoding="utf-8") as file:
                    text = file.read()
                    self.documents.append({
                        "filename": filename,
                        "text": text
                    })

        if not self.documents:
            print(f"Warning: no .txt files found in '{folder}'. "
                  "The agent will run without retrieval context.")
            return

        texts = [doc["text"] for doc in self.documents]
        embeddings = self.model.encode(texts)
        embeddings = np.array(embeddings).astype("float32")

        self.index = faiss.IndexFlatL2(
            embeddings.shape[1]
        )
        self.index.add(embeddings)

    def search(self, query, k=3):
        if self.index is None:
            return []

        query_embedding = self.model.encode(
            [query]
        )
        query_embedding = np.array(
            query_embedding
        ).astype("float32")

        distances, indices = self.index.search(
            query_embedding,
            k
        )

        results = []
        for index in indices[0]:
            if index != -1 and index < len(self.documents):
                results.append(
                    self.documents[index]
                )
        return results
