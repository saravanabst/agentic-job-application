import sys
from pathlib import Path


# ============================================================
# TEST IMPORT SETUP
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = BASE_DIR / "agents"

sys.path.insert(
    0,
    str(AGENTS_DIR)
)

import application_tracker


# ============================================================
# FIXTURE
# ============================================================

def create_test_application(tmp_path, deadline=None):
    """
    Redirect the tracker to an isolated temporary database
    and create one test application.
    """

    database_dir = tmp_path / "data"
    database_dir.mkdir()

    database_path = (
        database_dir
        / "test_applications.db"
    )

    application_tracker.DATABASE_DIR = database_dir
    application_tracker.DATABASE_PATH = database_path

    application_tracker.initialize_database()

    job = {
        "job_id": "test_tracker_001",
        "company": "Test Company",
        "job_title": "Data Analyst",
        "location": "Auckland",
        "work_mode": "Hybrid",
        "source": "test",
        "source_job_id": "test_source_001",
        "url": "https://example.com/job",
        "match_score": 90,
        "decision": "apply",
        "application_deadline": deadline,
    }

    result = application_tracker.add_application(
        job
    )

    assert result is True

    return "test_tracker_001"


# ============================================================
# VALID TRANSITION TEST
# ============================================================

def test_update_status_allows_valid_transition(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    result = application_tracker.update_status(
        job_id,
        "review_required"
    )

    assert result is True

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "review_required"


# ============================================================
# INVALID TRANSITION TEST
# ============================================================

def test_update_status_blocks_invalid_transition(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    result = application_tracker.update_status(
        job_id,
        "offer"
    )

    assert result is False

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "not_applied"


# ============================================================
# APPROVAL SAFETY TEST
# ============================================================

def test_approved_status_requires_human_approval(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    application_tracker.update_status(
        job_id,
        "application_prepared"
    )

    result = application_tracker.update_status(
        job_id,
        "approved"
    )

    assert result is False

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "application_prepared"


# ============================================================
# SUBMISSION SAFETY TEST
# ============================================================

def test_submitted_status_requires_human_approval(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    application_tracker.update_status(
        job_id,
        "application_prepared"
    )

    result = application_tracker.update_status(
        job_id,
        "approved"
    )

    assert result is False

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "application_prepared"


# ============================================================
# HUMAN APPROVAL THEN APPROVAL STATUS
# ============================================================

def test_human_approval_allows_approved_status(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    application_tracker.update_status(
        job_id,
        "application_prepared"
    )

    approval_result = (
        application_tracker.set_human_approval(
            job_id,
            True,
            "Automated Test Reviewer"
        )
    )

    assert approval_result is True

    result = application_tracker.update_status(
        job_id,
        "approved"
    )

    assert result is True

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "approved"

    assert bool(
        application["human_approved"]
    ) is True


# ============================================================
# SUBMISSION AFTER APPROVAL
# ============================================================

def test_human_approved_application_can_be_submitted(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    application_tracker.update_status(
        job_id,
        "application_prepared"
    )

    application_tracker.set_human_approval(
        job_id,
        True,
        "Automated Test Reviewer"
    )

    application_tracker.update_status(
        job_id,
        "approved"
    )

    result = application_tracker.update_status(
        job_id,
        "submitted"
    )

    assert result is True

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "submitted"

    assert application[
        "submitted_at"
    ] is not None


# ============================================================
# EXPIRED DEADLINE SAFETY
# ============================================================

def test_expired_deadline_blocks_submission(
    tmp_path
):

    job_id = create_test_application(
        tmp_path,
        "2020-01-01"
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    application_tracker.update_status(
        job_id,
        "application_prepared"
    )

    application_tracker.set_human_approval(
        job_id,
        True,
        "Automated Test Reviewer"
    )

    application_tracker.update_status(
        job_id,
        "approved"
    )

    result = application_tracker.update_status(
        job_id,
        "submitted"
    )

    assert result is False

    application = (
        application_tracker.get_application(
            job_id
        )
    )

    assert application[
        "application_status"
    ] == "approved"


# ============================================================
# STATUS HISTORY TEST
# ============================================================

def test_status_history_records_transition(
    tmp_path
):

    job_id = create_test_application(
        tmp_path
    )

    application_tracker.update_status(
        job_id,
        "review_required"
    )

    connection = (
        application_tracker.get_connection()
    )

    connection.row_factory = (
        application_tracker.sqlite3.Row
    )

    rows = connection.execute(
        """
        SELECT
            previous_status,
            new_status
        FROM application_status_history
        WHERE job_id = ?
        ORDER BY id
        """,
        (job_id,)
    ).fetchall()

    connection.close()

    assert len(rows) == 1

    assert rows[0]["previous_status"] == (
        "not_applied"
    )

    assert rows[0]["new_status"] == (
        "review_required"
    )