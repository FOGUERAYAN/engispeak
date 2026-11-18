import json
import logging

from engispeak.config import load_settings
from engispeak.logging_utils import JsonFormatter


def test_defaults_use_local_fallbacks(monkeypatch):
    for var in ("DATABASE_URL", "AZURE_STORAGE_ACCOUNT_URL", "KEY_VAULT_URL", "PROGRESS_BACKEND"):
        monkeypatch.delenv(var, raising=False)
    s = load_settings()
    assert s.database_url.startswith("sqlite:///")
    assert s.progress_backend == "sql"
    assert s.blob_enabled is False


def test_blob_enabled_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://example.blob.core.windows.net")
    assert load_settings().blob_enabled is True


def test_json_formatter_includes_extra_fields():
    record = logging.makeLogRecord({"msg": "reminder_sent", "levelname": "INFO", "student_id": "x"})
    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == "reminder_sent"
    assert payload["student_id"] == "x"
