"""
rag.py
Loads all .txt files from the knowledge_base/ folder (regulations, syllabus,
FAQs, notices — or any other categories you add), embeds them, and lets the
agent semantically search across them.

Each file is split into paragraph-sized chunks so retrieval returns focused,
relevant sections instead of an entire multi-topic file.
"""

import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


def _chunk_text(text: str, filename: str):
    """Split a document into paragraph chunks (blank-line separated)."""
    raw_chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    chunks = []
    for i, chunk in enumerate(raw_chunks):
        chunks.append({
            "filename": filename,
            "chunk_id": i,
            "text": chunk
        })
    return chunks


class KnowledgeBase:
    def __init__(self, folder="knowledge_base"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.documents = []
        self.index = None

        if not os.path.isdir(folder):
            print(f"Warning: knowledge base folder '{folder}' not found. "
                  "The assistant will run without retrieval context.")
            return

        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".txt"):
                continue
            path = os.path.join(folder, filename)
            with open(path, "r", encoding="utf-8") as file:
                text = file.read()
            self.documents.extend(_chunk_text(text, filename))

        if not self.documents:
            print(f"Warning: no .txt files found in '{folder}'. "
                  "The assistant will run without retrieval context.")
            return

        texts = [doc["text"] for doc in self.documents]
        embeddings = self.model.encode(texts)
        embeddings = np.array(embeddings).astype("float32")

        self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)

    def search(self, query: str, k: int = 4):
        """Return the top-k most relevant chunks for a query."""
        if self.index is None:
            return []

        query_embedding = self.model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, k)

        results = []
        for idx in indices[0]:
            if idx != -1 and idx < len(self.documents):
                results.append(self.documents[idx])
        return results