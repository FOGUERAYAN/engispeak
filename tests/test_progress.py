from datetime import UTC, datetime, timedelta

import pytest

from engispeak.progress import UnknownStepError, days_inactive, summarize, validate_step_id
from engispeak.roadmap import ALL_STEPS, ROADMAP

NOW = datetime(2026, 11, 20, 12, tzinfo=UTC)


def test_roadmap_structure():
    assert len(ROADMAP) == 4
    assert len(ALL_STEPS) == 16
    assert all(w.steps[-1].kind == "showcase" for w in ROADMAP)


def test_empty_progress():
    s = summarize({})
    assert (s.completed, s.total, s.percent) == (0, 16, 0)
    assert s.next_step.id == "w1-s1"
    assert s.current_week == 1
    assert s.last_activity is None


def test_week_one_completed_moves_to_week_two():
    progress = {step.id: NOW for step in ROADMAP[0].steps}
    s = summarize(progress)
    assert s.completed == 4
    assert s.percent == 25
    assert s.current_week == 2
    assert s.per_week[1] == (4, 4)
    assert s.next_step.id == "w2-s4"


def test_unknown_steps_are_ignored():
    s = summarize({"legacy-step": NOW, "w1-s1": NOW})
    assert s.completed == 1


def test_all_steps_finished():
    s = summarize({step.id: NOW for step in ALL_STEPS})
    assert s.finished and s.next_step is None and s.percent == 100


def test_days_inactive():
    s = summarize({"w1-s1": NOW - timedelta(days=3)})
    assert days_inactive(s, NOW) == 3


def test_validate_step_id():
    assert validate_step_id("w4-showcase") == "w4-showcase"
    with pytest.raises(UnknownStepError):
        validate_step_id("w5-s1")


def test_store_set_and_unset(store):
    store.set_step("bob", "w1-s1", True)
    store.set_step("bob", "w1-s1", True)  # idempotent
    assert set(store.get_progress("bob")) == {"w1-s1"}
    store.set_step("bob", "w1-s1", False)
    assert store.get_progress("bob") == {}
    assert store.list_students() == []
