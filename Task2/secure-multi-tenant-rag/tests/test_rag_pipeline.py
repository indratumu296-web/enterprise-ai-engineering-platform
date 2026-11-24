from types import SimpleNamespace
from unittest.mock import Mock, call

import src.rag_pipeline as rag_pipeline
import src.openai_config as openai_config
import src.query_rewriting as query_rewriting
from src.rag_pipeline import SecureRAGPipeline
from src.query_rewriting import QueryRewriter


def test_pipeline_uses_streamlit_secret_for_openai_key(monkeypatch):
    openai_factory = Mock()
    monkeypatch.setattr(
        openai_config,
        "st",
        SimpleNamespace(secrets={"OPENAI_API_KEY": "streamlit-key"}),
    )
    monkeypatch.setattr(rag_pipeline, "OpenAI", openai_factory)
    monkeypatch.setattr(query_rewriting, "OpenAI", openai_factory)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    pipeline = SecureRAGPipeline(retriever=None, reranker=None, rewriter=None)
    QueryRewriter()

    assert openai_factory.call_args_list == [
        call(api_key="streamlit-key"),
        call(api_key="streamlit-key"),
    ]
    assert pipeline.api_key == "streamlit-key"


def test_pipeline_falls_back_to_environment_openai_key(monkeypatch):
    openai_factory = Mock()
    monkeypatch.setattr(openai_config, "st", SimpleNamespace(secrets={}))
    monkeypatch.setattr(rag_pipeline, "OpenAI", openai_factory)
    monkeypatch.setattr(query_rewriting, "OpenAI", openai_factory)
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    SecureRAGPipeline(retriever=None, reranker=None, rewriter=None)
    QueryRewriter()

    assert len(openai_factory.call_args_list) == 2
    assert all(
        call.kwargs == {"api_key": "environment-key"}
        for call in openai_factory.call_args_list
    )


def test_streamlit_secrets_lookup_falls_back_when_secrets_are_unavailable(monkeypatch):
    class UnavailableSecrets:
        def get(self, key):
            raise FileNotFoundError

    monkeypatch.setattr(openai_config, "st", SimpleNamespace(secrets=UnavailableSecrets()))
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key")

    assert openai_config.get_openai_api_key() == "environment-key"


def test_generation_error_shows_details_without_exposing_api_key(monkeypatch):
    monkeypatch.setattr(
        rag_pipeline,
        "get_openai_api_key",
        lambda: "private-api-key",
    )
    monkeypatch.setattr(rag_pipeline, "OpenAI", Mock())
    pipeline = SecureRAGPipeline(retriever=None, reranker=None, rewriter=None)
    pipeline.rewriter = Mock()
    pipeline.rewriter.rewrite.return_value = "rewritten query"
    pipeline.retriever = Mock()
    pipeline.retriever.retrieve.return_value = [
        {
            "metadata": {
                "source": "policy.pdf",
                "page_number": 1,
            },
            "text": "Policy context",
        }
    ]
    pipeline.reranker = Mock()
    pipeline.reranker.rerank.side_effect = lambda **kwargs: kwargs["chunks"]
    pipeline.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=Mock(
                    side_effect=RuntimeError(
                        "Request failed using private-api-key"
                    )
                )
            )
        )
    )

    result = pipeline.run(query="question", user={})

    assert result["answer"].startswith("Answer generation failed: RuntimeError:")
    assert "[REDACTED]" in result["answer"]
    assert "private-api-key" not in result["answer"]
