"""Stockage 2 : ressources de cours (fiches mémo, guides).

- BlobResourceStore : Azure Blob Storage avec DefaultAzureCredential
  (Managed Identity en production, `az login` en local).
- LocalResourceStore : fallback sur un dossier local quand
  AZURE_STORAGE_ACCOUNT_URL n'est pas défini.
"""

from __future__ import annotations

import logging
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from engispeak.config import Settings

logger = logging.getLogger(__name__)


class ResourceNotFoundError(LookupError):
    pass


@dataclass(frozen=True)
class Resource:
    name: str
    size: int
    content_type: str


def _content_type(name: str) -> str:
    guessed, _ = mimetypes.guess_type(name)
    if name.endswith(".md"):
        return "text/markdown; charset=utf-8"
    return guessed or "application/octet-stream"


def _safe_name(name: str) -> str:
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise ResourceNotFoundError(name)
    return name


class ResourceStore(ABC):
    backend: str = "unknown"

    @abstractmethod
    def list_resources(self) -> list[Resource]: ...

    @abstractmethod
    def read(self, name: str) -> tuple[bytes, str]:
        """Retourne (contenu, content_type)."""


class LocalResourceStore(ResourceStore):
    backend = "local"

    def __init__(self, directory: str) -> None:
        self.directory = Path(directory)

    def list_resources(self) -> list[Resource]:
        if not self.directory.is_dir():
            return []
        return [
            Resource(p.name, p.stat().st_size, _content_type(p.name))
            for p in sorted(self.directory.iterdir())
            if p.is_file() and not p.name.startswith(".")
        ]

    def read(self, name: str) -> tuple[bytes, str]:
        path = self.directory / _safe_name(name)
        if not path.is_file():
            raise ResourceNotFoundError(name)
        return path.read_bytes(), _content_type(name)


class BlobResourceStore(ResourceStore):  # pragma: no cover - nécessite Azure
    backend = "azure_blob"

    def __init__(self, account_url: str, container: str) -> None:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        service = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())
        self.container = service.get_container_client(container)

    def list_resources(self) -> list[Resource]:
        return [
            Resource(
                b.name,
                b.size,
                (b.content_settings.content_type if b.content_settings else None) or _content_type(b.name),
            )
            for b in self.container.list_blobs()
        ]

    def read(self, name: str) -> tuple[bytes, str]:
        from azure.core.exceptions import ResourceNotFoundError as AzureNotFound

        blob = self.container.get_blob_client(_safe_name(name))
        try:
            data = blob.download_blob().readall()
        except AzureNotFound as exc:
            raise ResourceNotFoundError(name) from exc
        return data, _content_type(name)


def build_resource_store(settings: Settings) -> ResourceStore:
    if settings.blob_enabled:
        logger.info("Ressources : Azure Blob Storage", extra={"container": settings.azure_storage_container})
        return BlobResourceStore(settings.azure_storage_account_url, settings.azure_storage_container)
    logger.info("Ressources : dossier local (fallback)", extra={"dir": settings.local_resources_dir})
    return LocalResourceStore(settings.local_resources_dir)
