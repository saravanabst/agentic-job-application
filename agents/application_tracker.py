import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "applications" / "data"

DATABASE_PATH = DATABASE_DIR / "applications.db"


VALID_STATUSES = [
    "not_applied",
    "review_required",
    "approved",
    "application_prepared",
    "submitted",
    "rejected",
    "interview",
    "offer",
    "withdrawn"
]


def get_connection():
    """Create a database connection."""

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return sqlite3.connect(
        DATABASE_PATH
    )


def initialize_database():
    """Create the application tracking table."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_id TEXT NOT NULL,

            company TEXT NOT NULL,

            job_title TEXT NOT NULL,

            location TEXT,

            work_mode TEXT,

            source TEXT,

            source_job_id TEXT,

            job_url TEXT,

            match_score REAL,

            decision TEXT,

            application_status TEXT NOT NULL,

            discovered_at TEXT,

            approved_at TEXT,

            submitted_at TEXT,

            last_updated TEXT,

            resume_version TEXT,

            cover_letter_version TEXT,

            application_method TEXT,

            notes TEXT,

            UNIQUE(job_id)
        )
        """
    )

    connection.commit()

    connection.close()


def application_exists(job_id):
    """Check whether a job already exists."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, application_status
        FROM applications
        WHERE job_id = ?
        """,
        (job_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


def add_application(job):
    """
    Add a job to the application tracker.

    Duplicate job IDs are not inserted twice.
    """

    existing = application_exists(
        job["job_id"]
    )

    if existing:

        print(
            f"APPLICATION ALREADY EXISTS: "
            f"{job['job_id']}"
        )

        print(
            f"Current status: "
            f"{existing[1]}"
        )

        return False

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO applications (
            job_id,
            company,
            job_title,
            location,
            work_mode,
            source,
            source_job_id,
            job_url,
            match_score,
            decision,
            application_status,
            discovered_at,
            last_updated,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job.get("job_id"),
            job.get("company"),
            job.get("title"),
            job.get("location"),
            job.get("work_mode"),
            job.get("source"),
            job.get("source_job_id"),
            job.get("url"),
            job.get("match_score"),
            job.get("decision"),
            "not_applied",
            job.get(
                "discovered_at"
            ) or now,
            now,
            job.get("notes", "")
        )
    )

    connection.commit()

    connection.close()

    print(
        f"APPLICATION CREATED: "
        f"{job['job_id']}"
    )

    return True


def update_status(
    job_id,
    new_status
):
    """Update the application status."""

    if new_status not in VALID_STATUSES:

        raise ValueError(
            f"Invalid status: "
            f"{new_status}"
        )

    existing = application_exists(
        job_id
    )

    if not existing:

        print(
            f"Job not found: {job_id}"
        )

        return False

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE applications

        SET application_status = ?,
            last_updated = ?

        WHERE job_id = ?
        """,
        (
            new_status,
            now,
            job_id
        )
    )

    connection.commit()

    connection.close()

    print(
        f"STATUS UPDATED: "
        f"{job_id} -> {new_status}"
    )

    return True


def get_application(job_id):
    """Return one application."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE job_id = ?
        """,
        (job_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result


def list_applications():
    """Display all tracked applications."""

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            job_id,
            company,
            job_title,
            location,
            match_score,
            decision,
            application_status,
            last_updated
        FROM applications
        ORDER BY last_updated DESC
        """
    )

    applications = cursor.fetchall()

    connection.close()

    print()
    print(
        "APPLICATION TRACKER"
    )
    print("=" * 80)

    if not applications:

        print(
            "No applications tracked yet."
        )

        return

    for application in applications:

        (
            job_id,
            company,
            title,
            location,
            score,
            decision,
            status,
            updated
        ) = application

        print()
        print(
            f"Job ID:     {job_id}"
        )

        print(
            f"Company:    {company}"
        )

        print(
            f"Title:      {title}"
        )

        print(
            f"Location:   {location}"
        )

        print(
            f"Score:      {score}"
        )

        print(
            f"Decision:   {decision}"
        )

        print(
            f"Status:     {status}"
        )

        print(
            f"Updated:    {updated}"
        )


def main():

    print()
    print(
        "APPLICATION TRACKER TEST"
    )
    print("=" * 60)

    initialize_database()

    test_job = {
        "job_id": "job_001",
        "company": "Example Analytics Company",
        "title": "Data Analyst",
        "location": "Auckland, New Zealand",
        "work_mode": "Hybrid",
        "source": "test",
        "source_job_id": "TEST-001",
        "url": "",
        "match_score": 90,
        "decision": "PRIORITY APPLY",
        "discovered_at": "",
        "notes": "Initial test job"
    }

    print()
    print("Adding test job...")

    add_application(
        test_job
    )

    print()
    print("Trying to add the same job again...")

    add_application(
        test_job
    )

    print()
    print("Updating status...")

    update_status(
        "job_001",
        "review_required"
    )

    update_status(
        "job_001",
        "approved"
    )

    print()
    print("Current applications:")

    list_applications()


if __name__ == "__main__":
    main()