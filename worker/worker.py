"""Service 2 : worker EngiSpeak.

Tourne en tâche de fond (boucle) ou en tâche planifiée (WORKER_RUN_ONCE=true,
ex. Azure Container Apps Job / cron). Pour chaque étudiant, il analyse la
progression et simule l'envoi d'un rappel motivant (log structuré JSON).
"""

from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from engispeak.config import Settings, get_settings
from engispeak.logging_utils import setup_logging
from engispeak.progress import days_inactive, summarize
from engispeak.storage import ProgressStore, build_progress_store

logger = logging.getLogger("engispeak.worker")

MOTIVATION = {
    "start": "Ta roadmap t'attend ! Session 1 : regarde Chris Anderson et trouve ta throughline.",
    "inactive": "Ça fait {days} jours sans pratique. 20 minutes aujourd'hui suffisent : {step}.",
    "showcase": "C'est bientôt dimanche : prépare ta prise filmée ({step}).",
    "on_track": "Belle régularité ({percent} %). Prochaine étape : {step}.",
    "finished": "Roadmap terminée. Refais la keynote finale dans un mois pour mesurer tes progrès.",
}


@dataclass(frozen=True)
class Reminder:
    student_id: str
    kind: str
    message: str
    percent: int


def build_reminder(
    student_id: str,
    progress: dict[str, datetime],
    inactivity_threshold: int,
    now: datetime | None = None,
) -> Reminder:
    summary = summarize(progress)
    step = summary.next_step.title if summary.next_step else ""
    inactive = days_inactive(summary, now)

    if summary.finished:
        kind = "finished"
    elif summary.completed == 0:
        kind = "start"
    elif inactive is not None and inactive >= inactivity_threshold:
        kind = "inactive"
    elif summary.next_step and summary.next_step.kind == "showcase":
        kind = "showcase"
    else:
        kind = "on_track"

    message = MOTIVATION[kind].format(days=inactive, step=step, percent=summary.percent)
    return Reminder(student_id, kind, message, summary.percent)


def run_once(store: ProgressStore, settings: Settings, now: datetime | None = None) -> list[Reminder]:
    now = now or datetime.now(UTC)
    students = store.list_students()
    logger.info("cycle_start", extra={"students": len(students)})
    reminders = []
    for student_id in students:
        try:
            reminder = build_reminder(
                student_id, store.get_progress(student_id), settings.inactivity_days_threshold, now
            )
        except Exception:
            logger.exception("reminder_failed", extra={"student_id": student_id})
            continue
        # Simulation d'envoi : en production on brancherait ici un service
        # d'e-mail / notification (ex. Azure Communication Services).
        logger.info(
            "reminder_sent",
            extra={
                "student_id": reminder.student_id,
                "reminder_kind": reminder.kind,
                "progress_percent": reminder.percent,
                "reminder_message": reminder.message,
                "channel": "simulated",
            },
        )
        reminders.append(reminder)
    logger.info("cycle_end", extra={"reminders": len(reminders)})
    return reminders


def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    store = build_progress_store(settings)

    stop = {"requested": False}

    def _handle_stop(signum, _frame):
        logger.info("shutdown_requested", extra={"signal": signum})
        stop["requested"] = True

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    logger.info(
        "worker_started",
        extra={"run_once": settings.worker_run_once, "interval_s": settings.worker_interval_seconds},
    )
    while True:
        run_once(store, settings)
        if settings.worker_run_once:
            break
        deadline = time.monotonic() + settings.worker_interval_seconds
        while time.monotonic() < deadline and not stop["requested"]:
            time.sleep(1)
        if stop["requested"]:
            break
    logger.info("worker_stopped")


if __name__ == "__main__":
    main()
