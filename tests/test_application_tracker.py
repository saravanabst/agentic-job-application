import sys
from pathlib import Path


# Add agents directory to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = BASE_DIR / "agents"

sys.path.insert(
    0,
    str(AGENTS_DIR)
)

from application_tracker import (
    VALID_STATUSES,
    ALLOWED_STATUS_TRANSITIONS,
)


def test_all_application_statuses_are_defined():

    expected_statuses = {
        "not_applied",
        "review_required",
        "approved",
        "application_prepared",
        "submitted",
        "rejected",
        "interview",
        "offer",
        "withdrawn",
    }

    assert set(VALID_STATUSES) == expected_statuses


def test_not_applied_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["not_applied"] == [
        "review_required",
        "withdrawn",
    ]


def test_review_required_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["review_required"] == [
        "application_prepared",
        "withdrawn",
    ]


def test_application_prepared_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["application_prepared"] == [
        "approved",
        "withdrawn",
    ]


def test_approved_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["approved"] == [
        "submitted",
        "withdrawn",
        "review_required",
    ]


def test_submitted_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["submitted"] == [
        "rejected",
        "interview",
        "withdrawn",
    ]


def test_interview_transitions():

    assert ALLOWED_STATUS_TRANSITIONS["interview"] == [
        "offer",
        "withdrawn",
    ]


def test_offer_is_terminal():

    assert ALLOWED_STATUS_TRANSITIONS["offer"] == [
        "withdrawn",
    ]


def test_rejected_is_terminal():

    assert ALLOWED_STATUS_TRANSITIONS["rejected"] == []


def test_withdrawn_is_terminal():

    assert ALLOWED_STATUS_TRANSITIONS["withdrawn"] == []


def test_submitted_cannot_jump_directly_to_offer():

    assert "offer" not in (
        ALLOWED_STATUS_TRANSITIONS["submitted"]
    )


def test_submitted_cannot_jump_directly_to_approved():

    assert "approved" not in (
        ALLOWED_STATUS_TRANSITIONS["submitted"]
    )


def test_application_prepared_cannot_jump_directly_to_submitted():

    assert "submitted" not in (
        ALLOWED_STATUS_TRANSITIONS["application_prepared"]
    )


def test_interview_can_progress_to_offer():

    assert "offer" in (
        ALLOWED_STATUS_TRANSITIONS["interview"]
    )


def test_submitted_can_progress_to_interview():

    assert "interview" in (
        ALLOWED_STATUS_TRANSITIONS["submitted"]
    )


def test_submitted_can_be_rejected():

    assert "rejected" in (
        ALLOWED_STATUS_TRANSITIONS["submitted"]
    )


def test_every_status_has_transition_definition():

    for status in VALID_STATUSES:

        assert status in ALLOWED_STATUS_TRANSITIONS