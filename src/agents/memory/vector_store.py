import os
import uuid
from datetime import datetime
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()


class VectorStore:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found in environment variables.")

        self.client = chromadb.PersistentClient(path="./chroma_db")

        # Use Google Generative AI Embeddings
        # default model is usually models/embedding-001
        self.ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=api_key
        )

        self.collection = self.client.get_or_create_collection(
            name="vocabulary", embedding_function=self.ef
        )

    def add_phrase(
        self,
        text: str,
        translation: str,
        context: str,
        category: str,
        language: str = "dutch",
    ):
        """Adds a new phrase to the vector store."""
        now = datetime.now().isoformat()
        metadata = {
            "created_at": now,
            "last_review": now,
            "review_count": 0,
            "score": 0.0,
            "language": language,
            "category": category,
            "translation": translation,
            "context": context,
        }

        doc_id = str(uuid.uuid4())
        self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def search_phrases(self, query: str, n_results: int = 5, filter_dict: dict = None):
        """Searches for similar phrases."""
        # Simple query
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_dict,  # Optional filtering
        )

        # Formatting results for easier consumption
        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"][0])):
                item = {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": (
                        results["distances"][0][i] if results["distances"] else None
                    ),
                }
                formatted_results.append(item)

        return formatted_results

    def update_review_stats(self, doc_id: str, score: float):
        """Updates review statistics for a phrase."""
        # Fetch current metadata
        item = self.collection.get(ids=[doc_id])
        if item["metadatas"]:
            metadata = item["metadatas"][0]
            current_count = metadata.get("review_count", 0)

            metadata["review_count"] = current_count + 1
            metadata["last_review"] = datetime.now().isoformat()
            metadata["score"] = (
                score  # Could implement a moving average or weighted score
            )

            self.collection.update(ids=[doc_id], metadatas=[metadata])
