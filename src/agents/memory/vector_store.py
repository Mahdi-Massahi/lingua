import os
import uuid
import json
from datetime import datetime
import chromadb
from dotenv import load_dotenv
import google.generativeai as genai
from chromadb import Documents, EmbeddingFunction, Embeddings

load_dotenv()


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(
        self,
        api_key,
        model_name="models/gemini-embedding-001",
        dimension=768,
    ):
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.dimension = dimension

    def __call__(self, input: Documents) -> Embeddings:
        # This call sets the task_type and output_dimensionality
        result = genai.embed_content(
            model=self.model_name,
            content=input,
            task_type="retrieval_document",
            output_dimensionality=self.dimension,
        )
        return result["embedding"]


class VectorStore:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = chromadb.PersistentClient(path="./chroma_db")

        # Use the custom function to fix the dimension at 768
        self.ef = GeminiEmbeddingFunction(api_key=api_key, dimension=768)

        self.collection = self.client.get_or_create_collection(
            name="vocabulary",
            embedding_function=self.ef,
        )

    def add_phrase(
        self,
        text: str,
        translation: str,
        context: str,
        category: str,
        language: str = "dutch",
        reference: dict = None,
    ):
        """Adds a new phrase to the vector store."""
        now = datetime.now().isoformat()

        refs = []
        if reference:
            refs.append(reference)

        metadata = {
            "created_at": now,
            "last_review": now,
            "review_count": 0,
            "score": 0.0,
            "language": language,
            "category": category,
            "translation": translation,
            "context": context,
            "references": json.dumps(refs),
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

    def get_all_phrases(self, limit: int = 100):
        """Retrieves all phrases from the vector store."""
        results = self.collection.get(limit=limit)

        formatted_results = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                item = {
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i] if results["metadatas"] else {},
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

    def toggle_star(self, doc_id: str):
        """Toggles the 'starred' status of a phrase."""
        item = self.collection.get(ids=[doc_id])
        if item["metadatas"]:
            metadata = item["metadatas"][0]
            # Convert boolean to string or store as boolean if supported.
            # ChromaDB supports booleans, ints, floats, strings.
            current_status = metadata.get("starred", False)
            new_status = not current_status
            metadata["starred"] = new_status

            self.collection.update(ids=[doc_id], metadatas=[metadata])
            return new_status
        return False
