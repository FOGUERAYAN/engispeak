"""Stockage 1 : progression des étudiants.

- SqlProgressStore : SQLite en local / tests, PostgreSQL en production
  (même code, seule DATABASE_URL change).
- AzureTableProgressStore : Azure Table Storage via Managed Identity.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    select,
)
from sqlalchemy.dialects import postgresql, sqlite

from engispeak.config import Settings

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ProgressStore(ABC):
    @abstractmethod
    def get_progress(self, student_id: str) -> dict[str, datetime]:
        """Retourne {step_id: date de validation}."""

    @abstractmethod
    def set_step(self, student_id: str, step_id: str, completed: bool) -> None:
        """Valide ou dé-valide une étape."""

    @abstractmethod
    def list_students(self) -> list[str]:
        """Liste les étudiants ayant au moins une étape enregistrée."""

    def ping(self) -> bool:
        return True


metadata = MetaData()
progress_table = Table(
    "progress",
    metadata,
    Column("student_id", String(64), primary_key=True),
    Column("step_id", String(32), primary_key=True),
    Column("completed_at", DateTime(timezone=True), nullable=False),
)


class SqlProgressStore(ProgressStore):
    def __init__(self, database_url: str) -> None:
        if database_url.startswith("sqlite:///"):
            db_path = database_url.removeprefix("sqlite:///")
            if db_path and db_path != ":memory:":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(database_url, pool_pre_ping=True, future=True)
        metadata.create_all(self.engine)

    def get_progress(self, student_id: str) -> dict[str, datetime]:
        query = select(progress_table.c.step_id, progress_table.c.completed_at).where(
            progress_table.c.student_id == student_id
        )
        with self.engine.connect() as conn:
            rows = conn.execute(query).all()
        result = {}
        for step_id, completed_at in rows:
            if completed_at.tzinfo is None:  # SQLite ne conserve pas le fuseau
                completed_at = completed_at.replace(tzinfo=UTC)
            result[step_id] = completed_at
        return result

    def set_step(self, student_id: str, step_id: str, completed: bool) -> None:
        with self.engine.begin() as conn:
            if not completed:
                conn.execute(
                    delete(progress_table).where(
                        progress_table.c.student_id == student_id,
                        progress_table.c.step_id == step_id,
                    )
                )
                return
            values = {"student_id": student_id, "step_id": step_id, "completed_at": _utcnow()}
            dialect = self.engine.dialect.name
            if dialect == "postgresql":
                stmt = postgresql.insert(progress_table).values(**values)
            elif dialect == "sqlite":
                stmt = sqlite.insert(progress_table).values(**values)
            else:  # pragma: no cover
                raise RuntimeError(f"Base non supportée : {dialect}")
            conn.execute(stmt.on_conflict_do_nothing())

    def list_students(self) -> list[str]:
        query = select(progress_table.c.student_id).distinct()
        with self.engine.connect() as conn:
            return sorted(row[0] for row in conn.execute(query))

    def ping(self) -> bool:
        try:
            with self.engine.connect() as conn:
                conn.execute(select(1))
            return True
        except Exception:  # pragma: no cover
            logger.exception("Base de données injoignable")
            return False


class AzureTableProgressStore(ProgressStore):  # pragma: no cover - nécessite Azure
    """PartitionKey = student_id, RowKey = step_id."""

    def __init__(self, endpoint: str, table_name: str) -> None:
        from azure.data.tables import TableServiceClient
        from azure.identity import DefaultAzureCredential

        service = TableServiceClient(endpoint=endpoint, credential=DefaultAzureCredential())
        self.table = service.create_table_if_not_exists(table_name)

    def get_progress(self, student_id: str) -> dict[str, datetime]:
        entities = self.table.query_entities("PartitionKey eq @pk", parameters={"pk": student_id})
        return {e["RowKey"]: e["completed_at"] for e in entities}

    def set_step(self, student_id: str, step_id: str, completed: bool) -> None:
        if completed:
            self.table.upsert_entity(
                {"PartitionKey": student_id, "RowKey": step_id, "completed_at": _utcnow()}
            )
        else:
            self.table.delete_entity(partition_key=student_id, row_key=step_id)

    def list_students(self) -> list[str]:
        entities = self.table.list_entities(select=["PartitionKey"])
        return sorted({e["PartitionKey"] for e in entities})


def build_progress_store(settings: Settings) -> ProgressStore:
    if settings.progress_backend == "azure_table":
        if not settings.azure_table_endpoint:
            raise ValueError("PROGRESS_BACKEND=azure_table requiert AZURE_TABLE_ENDPOINT")
        logger.info("Stockage progression : Azure Table Storage")
        return AzureTableProgressStore(settings.azure_table_endpoint, settings.azure_table_name)
    backend = settings.database_url.split(":", 1)[0]
    logger.info("Stockage progression : SQL", extra={"backend": backend})
    return SqlProgressStore(settings.database_url)
