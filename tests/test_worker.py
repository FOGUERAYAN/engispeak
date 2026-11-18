from datetime import UTC, datetime, timedelta

from engispeak.roadmap import ALL_STEPS
from worker.worker import build_reminder, run_once

NOW = datetime(2026, 11, 20, 12, tzinfo=UTC)


def test_reminder_kinds():
    assert build_reminder("a", {}, 2, NOW).kind == "start"
    assert build_reminder("a", {"w1-s1": NOW - timedelta(days=5)}, 2, NOW).kind == "inactive"
    assert build_reminder("a", {"w1-s1": NOW}, 2, NOW).kind == "on_track"
    week1_sessions = {"w1-s1": NOW, "w1-s2": NOW, "w1-s3": NOW}
    assert build_reminder("a", week1_sessions, 2, NOW).kind == "showcase"
    assert build_reminder("a", {s.id: NOW for s in ALL_STEPS}, 2, NOW).kind == "finished"


def test_inactive_message_mentions_days():
    r = build_reminder("a", {"w1-s1": NOW - timedelta(days=4)}, 2, NOW)
    assert "4 jours" in r.message


def test_run_once_logs_one_reminder_per_student(store, settings, caplog):
    store.set_step("alice", "w1-s1", True)
    store.set_step("bob", "w1-s1", True)
    with caplog.at_level("INFO", logger="engispeak.worker"):
        reminders = run_once(store, settings)
    assert [r.student_id for r in reminders] == ["alice", "bob"]
    assert sum(1 for rec in caplog.records if rec.getMessage() == "reminder_sent") == 2
