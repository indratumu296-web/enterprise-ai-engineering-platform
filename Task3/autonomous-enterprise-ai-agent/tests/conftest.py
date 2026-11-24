from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from Database import db
from api.main import app


@pytest.fixture
def client(tmp_path, monkeypatch) -> Iterator[TestClient]:
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test-enterprise.db")
    with TestClient(app) as test_client:
        yield test_client
