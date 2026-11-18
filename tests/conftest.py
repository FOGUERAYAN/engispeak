from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from engispeak.config import load_settings
from engispeak.storage.progress_store import SqlProgressStore
from engispeak.storage.resource_store import LocalResourceStore
from web.app import create_app


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("LOCAL_RESOURCES_DIR", str(tmp_path / "resources"))
    monkeypatch.delenv("AZURE_STORAGE_ACCOUNT_URL", raising=False)
    monkeypatch.delenv("KEY_VAULT_URL", raising=False)
    return load_settings()


@pytest.fixture
def store(settings):
    return SqlProgressStore(settings.database_url)


@pytest.fixture
def resources(tmp_path):
    folder = tmp_path / "resources"
    folder.mkdir()
    (folder / "fiche-test.md").write_text("# Fiche test", encoding="utf-8")
    return LocalResourceStore(str(folder))


@pytest.fixture
def client(settings, store, resources):
    app = create_app(settings=settings, progress_store=store, resource_store=resources)
    return TestClient(app)


@pytest.fixture
def logged_client(client):
    client.post("/login", data={"student_id": "rayan"}, follow_redirects=False)
    return client
