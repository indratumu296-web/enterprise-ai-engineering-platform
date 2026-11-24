from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

class DocumentReranker:
    """
    Reranks candidate chunks using a cross-encoder model.
    """

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
        """
        Scores question-passage pairs and returns top_n most relevant chunks.
        """
        if not chunks:
            return []

        pairs = [[query, chunk["text"]] for chunk in chunks]
        scores = self.model.predict(pairs)

        for chunk, score in zip(chunks, scores):
            chunk["score"] = float(score)

        sorted_chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)
        return sorted_chunks[:top_n]