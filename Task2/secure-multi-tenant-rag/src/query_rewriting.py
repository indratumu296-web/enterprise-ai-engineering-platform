from openai import AuthenticationError, OpenAI
from src.openai_config import get_openai_api_key

class QueryRewriter:
    """
    Expands and clarifies raw user questions into optimized search queries.
    """

    def __init__(self, api_key: str = None):
        key = api_key or get_openai_api_key()
        self.client = OpenAI(api_key=key) if key else None

    def rewrite(self, query: str) -> str:
        """
        Rewrites an ambiguous query into a well-formulated search prompt.
        Falls back to original query if LLM is unavailable.
        """
        if not self.client:
            return query

        system_prompt = (
            "You are an AI search query optimizer for an enterprise RAG system. "
            "Your job is to rewrite vague or ambiguous user questions into clear, "
            "standalone search queries optimized for vector database retrieval. "
            "Preserve original intent. Do not answer the question."
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original Query: {query}"}
                ],
                temperature=0.0
            )
            rewritten = response.choices[0].message.content.strip()
            return rewritten if rewritten else query
        except AuthenticationError:
            raise
        except Exception:
            return query