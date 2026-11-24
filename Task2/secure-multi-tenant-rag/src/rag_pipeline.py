import re
from typing import Dict, Any
from openai import AuthenticationError, OpenAI
from src.openai_config import get_openai_api_key
from src.query_rewriting import QueryRewriter
from src.retrieval import VectorRetriever
from src.reranking import DocumentReranker

class SecureRAGPipeline:
    """
    End-to-end RAG orchestrator integrating rewriting, secure retrieval, reranking, and grounded generation.
    """

    def __init__(self, retriever: VectorRetriever, reranker: DocumentReranker, rewriter: QueryRewriter):
        self.retriever = retriever
        self.reranker = reranker
        self.rewriter = rewriter
        api_key = get_openai_api_key()
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key) if api_key else None

    def run(self, query: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes complete secure pipeline for a given user question and context.
        """
        # Step 1: Query Rewriting
        invalid_api_key = False
        try:
            rewritten_query = self.rewriter.rewrite(query)
        except AuthenticationError:
            rewritten_query = query
            invalid_api_key = True

        
        candidate_chunks = self.retriever.retrieve(query=rewritten_query, user=user, top_k=10)

        if not candidate_chunks:
            answer = (
                "OpenAI rejected the configured API key. Set OPENAI_API_KEY to a valid key "
                "in .streamlit/secrets.toml or the environment, then restart Streamlit."
                if invalid_api_key
                else "I do not have sufficient authorized context to answer your question."
            )
            return {
                "answer": answer,
                "citations": [],
                "rewritten_query": rewritten_query
            }

        # Step 5: Reranking
        ranked_chunks = self.reranker.rerank(query=rewritten_query, chunks=candidate_chunks, top_n=3)

        # Step 6: Grounded Generation
        context_str = ""
        citations = []
        for c in ranked_chunks:
            meta = c["metadata"]
            citation = f"[{meta['source']}, page {meta['page_number']}]"
            citations.append(citation)
            context_str += f"\n--- CHUNK {citation} ---\n{c['text']}\n"

        system_prompt = (
            "You are a strictly grounded enterprise support assistant. "
            "Answer the question ONLY using the provided evidence context below. "
            "You MUST cite exact source filenames and page numbers in brackets like "
            "[filename, page 5] for every factual claim made. "
            "If the context does not contain enough information, "
            "state clearly that you do not have sufficient evidence to answer."
        )

        user_prompt = f"Context:\n{context_str}\n\nQuestion: {query}"

        if invalid_api_key:
            answer = (
                "OpenAI rejected the configured API key. Set OPENAI_API_KEY to a valid key "
                "in .streamlit/secrets.toml or the environment, then restart Streamlit."
            )
        elif not self.client:
            return {
                "answer": (
                    "OPENAI_API_KEY is not configured. Add a valid key to "
                    ".streamlit/secrets.toml or the environment, then restart Streamlit."
                ),
                "citations": citations,
                "rewritten_query": rewritten_query
            }
        else:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0
                )
                answer = response.choices[0].message.content.strip()
            except AuthenticationError:
                answer = (
                    "OpenAI rejected the configured API key. Set OPENAI_API_KEY to a valid key "
                    "in .streamlit/secrets.toml or the environment, then restart Streamlit."
                )
            except Exception as exc:
                error_detail = str(exc)
                if self.api_key:
                    error_detail = error_detail.replace(self.api_key, "[REDACTED]")
                error_detail = re.sub(
                    r"(?i)(api[_ -]?key\s*[:=]\s*)[^\s,;]+",
                    r"\1[REDACTED]",
                    error_detail,
                )
                answer = (
                    f"Answer generation failed: {type(exc).__name__}: {error_detail}"
                )

        return {
            "answer": answer,
            "citations": list(set(citations)),
            "rewritten_query": rewritten_query
        }