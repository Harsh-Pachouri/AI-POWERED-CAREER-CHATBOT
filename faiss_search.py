import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class AIResourceSearch:
    def __init__(self, index_path="faiss.index"):
        self.model = SentenceTransformer("all-MiniLM-L12-v2")  # Fast & accurate model
        self.index_path = index_path
        self.index = faiss.IndexFlatL2(384)  # 384-dim vector space
        self.resources = []

        # Load FAISS index if available
        self.load_index()

    def add_to_index(self, link, description):
        vector = self.model.encode([description])[0]
        self.index.add(np.array([vector]))
        self.resources.append((link, description))
        self.save_index()  # Save the updated index

    def search(self, query):
        if not self.resources:
            return None  # No resources in the index

        query_vector = self.model.encode([query])[0]
        distances, indices = self.index.search(np.array([query_vector]), k=1)

        if len(indices) > 0 and len(indices[0]) > 0:
            index = indices[0][0]
            if index < len(self.resources):
                return self.resources[index][0]  # Return best-matched link
        return None  # No match found

    def save_index(self):
        """Save the FAISS index to a file."""
        faiss.write_index(self.index, self.index_path)

    def load_index(self):
        """Load the FAISS index from a file if it exists."""
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)

# Usage example:
if __name__ == "__main__":
    search_engine = AIResourceSearch()
    search_engine.add_to_index("https://example.com", "Machine learning tutorial")
    print(search_engine.search("ML basics"))
