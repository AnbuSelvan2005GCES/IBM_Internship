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

        for filename in os.listdir(folder):

            path = os.path.join(folder, filename)

            if filename.endswith(".txt"):

                with open(path, "r", encoding="utf-8") as file:

                    text = file.read()

                    self.documents.append({
                        "filename": filename,
                        "text": text
                    })

        texts = [doc["text"] for doc in self.documents]

        embeddings = self.model.encode(texts)

        embeddings = np.array(embeddings).astype("float32")

        self.index = faiss.IndexFlatL2(
            embeddings.shape[1]
        )

        self.index.add(embeddings)


    def search(self, query, k=3):

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

            if index < len(self.documents):

                results.append(
                    self.documents[index]
                )

        return results