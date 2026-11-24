import pytest
from src.security import SecurityManager
from src.retrieval import VectorRetriever

@pytest.fixture
def mock_vector_db(tmp_path):
    retriever = VectorRetriever(persist_directory=str(tmp_path), collection_name="test_rbac")
    
    # Insert test data across clients and departments
    test_chunks = [
        {
            "text": "Client A HR leave policy allows 20 days off.",
            "metadata": {"tenant_id": "client_a", "department": "HR", "clearance_level": 2, "source": "hr_policy.pdf", "page_number": 5}
        },
        {
            "text": "Client A Finance budget for 2024 is 10 million.",
            "metadata": {"tenant_id": "client_a", "department": "Finance", "clearance_level": 1, "source": "finance.pdf", "page_number": 1}
        },
        {
            "text": "Client B HR leave policy allows 15 days off.",
            "metadata": {"tenant_id": "client_b", "department": "HR", "clearance_level": 1, "source": "hr_b.pdf", "page_number": 2}
        }
    ]
    retriever.add_documents(test_chunks)
    return retriever

def test_tenant_isolation(mock_vector_db):
    user_a = {"user_id": "u1", "tenant_id": "client_a", "department": "HR", "clearance_level": 2}
    results = mock_vector_db.retrieve(query="leave policy", user=user_a)
    
    assert len(results) > 0
    for chunk in results:
        assert chunk["metadata"]["tenant_id"] == "client_a"
        assert chunk["metadata"]["tenant_id"] != "client_b"

def test_department_restriction(mock_vector_db):
    finance_user = {"user_id": "u2", "tenant_id": "client_a", "department": "Finance", "clearance_level": 2}
    results = mock_vector_db.retrieve(query="budget", user=finance_user)
    
    assert len(results) > 0
    assert all(chunk["metadata"]["department"] == "Finance" for chunk in results)

def test_clearance_level_restriction(mock_vector_db):
    low_clearance_hr_user = {"user_id": "u3", "tenant_id": "client_a", "department": "HR", "clearance_level": 1}
    results = mock_vector_db.retrieve(query="leave policy", user=low_clearance_hr_user)
    
    # The HR doc requires clearance level 2, user has 1
    assert len(results) == 0