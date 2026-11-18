"""Logique métier de progression (indépendante du stockage)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from engispeak.roadmap import ALL_STEPS, ROADMAP, STEP_IDS, Step


class UnknownStepError(ValueError):
    """L'identifiant d'étape n'existe pas dans la roadmap."""


def validate_step_id(step_id: str) -> str:
    if step_id not in STEP_IDS:
        raise UnknownStepError(f"Étape inconnue : {step_id}")
    return step_id


@dataclass(frozen=True)
class ProgressSummary:
    completed: int
    total: int
    percent: int
    current_week: int
    next_step: Step | None
    last_activity: datetime | None
    per_week: dict[int, tuple[int, int]]

    @property
    def finished(self) -> bool:
        return self.completed == self.total


def summarize(completed_steps: dict[str, datetime]) -> ProgressSummary:
    """Calcule l'avancement à partir des étapes validées {step_id: date}."""
    done = {sid for sid in completed_steps if sid in STEP_IDS}
    total = len(ALL_STEPS)
    per_week = {
        week.number: (sum(1 for s in week.steps if s.id in done), len(week.steps)) for week in ROADMAP
    }
    next_step = next((s for s in ALL_STEPS if s.id not in done), None)
    current_week = next(
        (w.number for w in ROADMAP if per_week[w.number][0] < per_week[w.number][1]),
        ROADMAP[-1].number,
    )
    last_activity = max(completed_steps.values()) if completed_steps else None
    return ProgressSummary(
        completed=len(done),
        total=total,
        percent=round(100 * len(done) / total),
        current_week=current_week,
        next_step=next_step,
        last_activity=last_activity,
        per_week=per_week,
    )


def days_inactive(summary: ProgressSummary, now: datetime | None = None) -> int | None:
    if summary.last_activity is None:
        return None
    now = now or datetime.now(UTC)
    last = summary.last_activity
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return (now - last).days
