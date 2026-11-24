from typing import List, Dict, Any
import chromadb
from chromadb.utils import embedding_functions
from src.security import SecurityManager

class VectorRetriever:
    """
    Manages vector embeddings, database persistence, and secure pre-filtered retrieval.
    """

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "enterprise_docs"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    def add_documents(self, chunks: List[Dict[str, Any]]):
        """
        Stores document chunks and associated metadata into ChromaDB.
        """
        documents = []
        metadatas = []
        ids = []

        for idx, item in enumerate(chunks):
            documents.append(item["text"])
            metadatas.append(item["metadata"])
            ids.append(f"{item['metadata']['source']}_p{item['metadata']['page_number']}_c{idx}")

        if documents:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

    def retrieve(self, query: str, user: Dict[str, Any], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves candidate documents after applying mandatory security filters.
        """
        where_clause = SecurityManager.build_security_filter(user)

        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )

        retrieved_chunks = []
        if results and results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                retrieved_chunks.append({
                    "text": doc,
                    "metadata": meta
                })

        return retrieved_chunks