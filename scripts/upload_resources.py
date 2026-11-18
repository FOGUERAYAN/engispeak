"""Envoie les fiches du dossier local vers le conteneur Azure Blob.

Usage (après `az login` ou avec une Managed Identity) :
    AZURE_STORAGE_ACCOUNT_URL=https://<compte>.blob.core.windows.net \
    python -m scripts.upload_resources
"""

from __future__ import annotations

import mimetypes
import sys
from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

from engispeak.config import load_settings


def main() -> int:
    settings = load_settings()
    if not settings.blob_enabled:
        print("AZURE_STORAGE_ACCOUNT_URL n'est pas défini.", file=sys.stderr)
        return 1
    service = BlobServiceClient(settings.azure_storage_account_url, credential=DefaultAzureCredential())
    container = service.get_container_client(settings.azure_storage_container)
    if not container.exists():
        container.create_container()
    for path in sorted(Path(settings.local_resources_dir).glob("*")):
        if not path.is_file():
            continue
        content_type = mimetypes.guess_type(path.name)[0] or "text/markdown"
        with path.open("rb") as fh:
            container.upload_blob(
                path.name, fh, overwrite=True, content_settings=ContentSettings(content_type=content_type)
            )
        print(f"Envoyé : {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
