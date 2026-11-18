"""Configuration 12-Factor : tout passe par des variables d'environnement.

Aucun secret n'est écrit dans le code. En production, les secrets (ex. la
chaîne de connexion PostgreSQL) peuvent être lus dans Azure Key Vault via
Managed Identity si KEY_VAULT_URL est défini.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

logger = logging.getLogger(__name__)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_key_vault_secret(vault_url: str, secret_name: str) -> str | None:
    """Lit un secret dans Azure Key Vault avec DefaultAzureCredential."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        client = SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
        return client.get_secret(secret_name).value
    except Exception as exc:  # pragma: no cover - dépend d'Azure
        logger.warning("Lecture Key Vault impossible (%s) : %s", secret_name, exc)
        return None


@dataclass(frozen=True)
class Settings:
    app_env: str
    log_level: str
    # Stockage 1 : progression
    progress_backend: str  # "sql" | "azure_table"
    database_url: str
    azure_table_endpoint: str | None
    azure_table_name: str
    # Stockage 2 : ressources de cours
    azure_storage_account_url: str | None
    azure_storage_container: str
    local_resources_dir: str
    # Secrets
    key_vault_url: str | None
    # Worker
    worker_interval_seconds: int
    worker_run_once: bool
    inactivity_days_threshold: int

    @property
    def blob_enabled(self) -> bool:
        return bool(self.azure_storage_account_url)


def load_settings() -> Settings:
    key_vault_url = _env("KEY_VAULT_URL")

    database_url = _env("DATABASE_URL")
    if database_url is None and key_vault_url:
        secret_name = _env("DATABASE_URL_SECRET_NAME", "database-url")
        database_url = _read_key_vault_secret(key_vault_url, secret_name)
    if database_url is None:
        database_url = "sqlite:///./data/engispeak.db"

    return Settings(
        app_env=_env("APP_ENV", "local"),
        log_level=_env("LOG_LEVEL", "INFO"),
        progress_backend=_env("PROGRESS_BACKEND", "sql"),
        database_url=database_url,
        azure_table_endpoint=_env("AZURE_TABLE_ENDPOINT"),
        azure_table_name=_env("AZURE_TABLE_NAME", "progress"),
        azure_storage_account_url=_env("AZURE_STORAGE_ACCOUNT_URL"),
        azure_storage_container=_env("AZURE_STORAGE_CONTAINER", "resources"),
        local_resources_dir=_env("LOCAL_RESOURCES_DIR", "./resources"),
        key_vault_url=key_vault_url,
        worker_interval_seconds=int(_env("WORKER_INTERVAL_SECONDS", "86400")),
        worker_run_once=_env_bool("WORKER_RUN_ONCE", False),
        inactivity_days_threshold=int(_env("INACTIVITY_DAYS_THRESHOLD", "2")),
    )


@lru_cache
def get_settings() -> Settings:
    return load_settings()
