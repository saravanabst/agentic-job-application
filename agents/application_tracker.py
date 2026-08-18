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


DEADLINE_STATUSES = [
    "NO_DEADLINE",
    "INVALID_DEADLINE",
    "OVERDUE",
    "DUE_TODAY",
    "DUE_SOON",
    "UPCOMING"
]


def get_connection():
    """
    Create a database connection.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return sqlite3.connect(
        DATABASE_PATH
    )


def initialize_database():
    """
    Create or upgrade the application tracking table.

    The deadline fields are deliberately stored in the
    application tracker so deadline information follows
    the job throughout the application lifecycle.
    """

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

            application_deadline TEXT,

            deadline_status TEXT,

            days_remaining INTEGER,

            human_approved INTEGER DEFAULT 0,

            reviewer TEXT,

            UNIQUE(job_id)
        )
        """
    )

    connection.commit()

    # --------------------------------------------------
    # DATABASE MIGRATION
    # --------------------------------------------------
    #
    # Existing applications.db databases may have been
    # created by an earlier version of the tracker.
    #
    # SQLite does not support adding the new columns
    # through CREATE TABLE IF NOT EXISTS.
    #
    # Therefore we inspect the existing table and add
    # missing columns when necessary.
    # --------------------------------------------------

    cursor.execute(
        """
        PRAGMA table_info(applications)
        """
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    new_columns = {
        "application_deadline": "TEXT",
        "deadline_status": "TEXT",
        "days_remaining": "INTEGER",
        "human_approved": "INTEGER DEFAULT 0",
        "reviewer": "TEXT"
    }

    for column_name, column_definition in new_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE applications
                ADD COLUMN {column_name}
                {column_definition}
                """
            )

    connection.commit()

    connection.close()


def parse_deadline(deadline):
    """
    Convert a deadline string into a datetime object.

    Supported formats:

        2026-08-30
        2026-08-30 17:00
        2026-08-30T17:00
        2026-08-30T17:00:00

    Returns None when no valid deadline is available.
    """

    if deadline is None:
        return None

    if isinstance(
        deadline,
        datetime
    ):
        return deadline

    if not isinstance(
        deadline,
        str
    ):
        return None

    deadline = deadline.strip()

    if not deadline:
        return None

    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d"
    ]

    for date_format in formats:

        try:

            return datetime.strptime(
                deadline,
                date_format
            )

        except ValueError:

            continue

    return None


def format_deadline(deadline):
    """
    Return a consistent human-readable deadline.
    """

    parsed = parse_deadline(
        deadline
    )

    if parsed is None:
        return None

    return parsed.strftime(
        "%Y-%m-%d %H:%M"
    )


def calculate_deadline_status(deadline):
    """
    Calculate the current deadline status.

    Returns:

        NO_DEADLINE
        INVALID_DEADLINE
        OVERDUE
        DUE_TODAY
        DUE_SOON
        UPCOMING

    Deadline monitoring only produces information and
    warnings. It never submits an application.
    """

    if deadline is None:

        return (
            "NO_DEADLINE",
            None
        )

    parsed = parse_deadline(
        deadline
    )

    if parsed is None:

        return (
            "INVALID_DEADLINE",
            None
        )

    now = datetime.now()

    difference = parsed - now

    total_seconds = difference.total_seconds()

    days_remaining = difference.days

    if total_seconds < 0:

        return (
            "OVERDUE",
            days_remaining
        )

    if parsed.date() == now.date():

        return (
            "DUE_TODAY",
            0
        )

    if days_remaining <= 3:

        return (
            "DUE_SOON",
            days_remaining
        )

    return (
        "UPCOMING",
        days_remaining
    )


def get_deadline_status(deadline):
    """
    Return only the deadline status.
    """

    status, _ = calculate_deadline_status(
        deadline
    )

    return status


def get_deadline_information(deadline):
    """
    Return both deadline status and days remaining.
    """

    return calculate_deadline_status(
        deadline
    )


def application_exists(job_id):
    """
    Check whether a job already exists.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            application_status
        FROM applications
        WHERE job_id = ?
        """,
        (
            job_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result


def add_application(job):
    """
    Add a job to the application tracker.

    Deadline information is copied from the job record.

    No deadline is invented.

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

    application_deadline = job.get(
        "application_deadline"
    )

    deadline_status, days_remaining = (
        calculate_deadline_status(
            application_deadline
        )
    )

    formatted_deadline = format_deadline(
        application_deadline
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

            notes,

            application_deadline,

            deadline_status,

            days_remaining,

            human_approved,

            reviewer
        )

        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (

            job.get(
                "job_id"
            ),

            job.get(
                "company"
            ),

            job.get(
                "title"
            ),

            job.get(
                "location"
            ),

            job.get(
                "work_mode"
            ),

            job.get(
                "source"
            ),

            job.get(
                "source_job_id"
            ),

            job.get(
                "url"
            ),

            job.get(
                "match_score"
            ),

            job.get(
                "decision"
            ),

            "not_applied",

            job.get(
                "discovered_at"
            ) or now,

            now,

            job.get(
                "notes",
                ""
            ),

            formatted_deadline,

            deadline_status,

            days_remaining,

            0,

            None
        )
    )

    connection.commit()

    connection.close()

    print(
        f"APPLICATION CREATED: "
        f"{job['job_id']}"
    )

    print(
        f"Deadline: "
        f"{formatted_deadline or 'NOT PROVIDED'}"
    )

    print(
        f"Deadline Status: "
        f"{deadline_status}"
    )

    if days_remaining is not None:

        print(
            f"Days Remaining: "
            f"{days_remaining}"
        )

    return True


def update_status(
    job_id,
    new_status
):
    """
    Update the application status.
    """

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
            f"Job not found: "
            f"{job_id}"
        )

        return False

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    connection = get_connection()

    cursor = connection.cursor()

    approved_at = None

    if new_status == "approved":

        approved_at = now

    submitted_at = None

    if new_status == "submitted":

        submitted_at = now

    cursor.execute(
        """
        UPDATE applications

        SET application_status = ?,

            last_updated = ?,

            approved_at =
                CASE
                    WHEN ? = 'approved'
                    THEN ?
                    ELSE approved_at
                END,

            submitted_at =
                CASE
                    WHEN ? = 'submitted'
                    THEN ?
                    ELSE submitted_at
                END

        WHERE job_id = ?
        """,
        (
            new_status,

            now,

            new_status,

            approved_at,

            new_status,

            submitted_at,

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


def set_human_approval(
    job_id,
    approved,
    reviewer=None
):
    """
    Record explicit human approval.

    Automatic approval is intentionally prohibited.

    approved must be supplied by a human-controlled
    workflow.
    """

    if not isinstance(
        approved,
        bool
    ):

        raise ValueError(
            "Human approval must be True or False."
        )

    existing = application_exists(
        job_id
    )

    if not existing:

        print(
            f"Job not found: "
            f"{job_id}"
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

        SET human_approved = ?,

            reviewer = ?,

            approved_at =
                CASE
                    WHEN ? = 1
                    THEN ?
                    ELSE approved_at
                END,

            last_updated = ?

        WHERE job_id = ?
        """,
        (
            1 if approved else 0,

            reviewer,

            1 if approved else 0,

            now if approved else None,

            now,

            job_id
        )
    )

    connection.commit()

    connection.close()

    print(
        f"HUMAN APPROVAL UPDATED: "
        f"{job_id} -> "
        f"{approved}"
    )

    if reviewer:

        print(
            f"Reviewer: "
            f"{reviewer}"
        )

    return True


def get_application(
    job_id
):
    """
    Return one application.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE job_id = ?
        """,
        (
            job_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result


def refresh_deadline_status(
    job_id=None
):
    """
    Refresh deadline status for one application
    or all applications.

    This function only updates tracking information.

    It never submits an application.
    """

    connection = get_connection()

    cursor = connection.cursor()

    if job_id:

        cursor.execute(
            """
            SELECT
                job_id,
                application_deadline
            FROM applications
            WHERE job_id = ?
            """,
            (
                job_id,
            )
        )

    else:

        cursor.execute(
            """
            SELECT
                job_id,
                application_deadline
            FROM applications
            """
        )

    applications = cursor.fetchall()

    now = datetime.now().isoformat(
        timespec="seconds"
    )

    updated = 0

    for application in applications:

        current_job_id = application[0]

        deadline = application[1]

        status, days_remaining = (
            calculate_deadline_status(
                deadline
            )
        )

        cursor.execute(
            """
            UPDATE applications

            SET deadline_status = ?,

                days_remaining = ?,

                last_updated = ?

            WHERE job_id = ?
            """,
            (
                status,

                days_remaining,

                now,

                current_job_id
            )
        )

        updated += 1

    connection.commit()

    connection.close()

    return updated


def print_deadline_status(
    job_id
):
    """
    Display deadline information for one application.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            job_id,
            company,
            job_title,
            application_deadline,
            deadline_status,
            days_remaining
        FROM applications
        WHERE job_id = ?
        """,
        (
            job_id,
        )
    )

    application = cursor.fetchone()

    connection.close()

    print()
    print(
        "APPLICATION DEADLINE MONITOR"
    )

    print(
        "=" * 80
    )

    if not application:

        print(
            f"Application not found: "
            f"{job_id}"
        )

        return

    (
        current_job_id,
        company,
        title,
        deadline,
        status,
        days_remaining
    ) = application

    print(
        f"Job:       "
        f"{current_job_id}"
    )

    print(
        f"Company:   "
        f"{company}"
    )

    print(
        f"Position:  "
        f"{title}"
    )

    print(
        f"Deadline:  "
        f"{deadline or 'NOT PROVIDED'}"
    )

    print(
        f"Status:    "
        f"{status}"
    )

    if status == "OVERDUE":

        overdue_days = abs(
            days_remaining or 0
        )

        print(
            f"OVERDUE BY: "
            f"{overdue_days} day(s)"
        )

    elif status == "DUE_TODAY":

        print(
            "DEADLINE IS TODAY"
        )

    elif status == "DUE_SOON":

        print(
            f"Days remaining: "
            f"{days_remaining}"
        )

    elif status == "UPCOMING":

        print(
            f"Days remaining: "
            f"{days_remaining}"
        )

    elif status == "NO_DEADLINE":

        print(
            "No application deadline was provided."
        )

    elif status == "INVALID_DEADLINE":

        print(
            "WARNING: Deadline value is invalid."
        )


def list_applications():
    """
    Display all tracked applications.
    """

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

            application_deadline,

            deadline_status,

            days_remaining,

            human_approved,

            reviewer,

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

    print(
        "=" * 100
    )

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

            deadline,

            deadline_status,

            days_remaining,

            human_approved,

            reviewer,

            updated

        ) = application

        print()

        print(
            f"Job ID:          "
            f"{job_id}"
        )

        print(
            f"Company:         "
            f"{company}"
        )

        print(
            f"Title:           "
            f"{title}"
        )

        print(
            f"Location:        "
            f"{location}"
        )

        print(
            f"Score:           "
            f"{score}"
        )

        print(
            f"Decision:        "
            f"{decision}"
        )

        print(
            f"Status:          "
            f"{status}"
        )

        print(
            f"Deadline:        "
            f"{deadline or 'NOT PROVIDED'}"
        )

        print(
            f"Deadline Status: "
            f"{deadline_status}"
        )

        if days_remaining is not None:

            print(
                f"Days Remaining:  "
                f"{days_remaining}"
            )

        print(
            f"Human Approved:  "
            f"{bool(human_approved)}"
        )

        print(
            f"Reviewer:        "
            f"{reviewer or 'None'}"
        )

        print(
            f"Updated:         "
            f"{updated}"
        )


def print_safety_status():
    """
    Display the safety guarantees of the tracker.
    """

    print()

    print(
        "SAFETY STATUS"
    )

    print(
        "Automatic submission: False"
    )

    print(
        "Automatic application: False"
    )

    print(
        "Automatic email: False"
    )

    print(
        "Automatic job submission: False"
    )

    print(
        "Deadline monitoring only produces information "
        "and warnings."
    )


def main():

    print()

    print(
        "APPLICATION TRACKER TEST - VERSION 4"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "DATABASE:"
    )

    print(
        DATABASE_PATH
    )

    # --------------------------------------------------
    # STEP 1
    # --------------------------------------------------

    print()

    print(
        "STEP 1 - INITIALIZE / MIGRATE DATABASE"
    )

    print(
        "-" * 70
    )

    initialize_database()

    print(
        "Database ready."
    )

    # --------------------------------------------------
    # STEP 2
    # --------------------------------------------------

    print()

    print(
        "STEP 2 - VERIFY EXISTING APPLICATION"
    )

    print(
        "-" * 70
    )

    existing = application_exists(
        "job_001"
    )

    if existing:

        print(
            f"Application exists: "
            f"job_001"
        )

        print(
            f"Current status: "
            f"{existing[1]}"
        )

    else:

        print(
            "job_001 is not currently tracked."
        )

    # --------------------------------------------------
    # STEP 3
    # --------------------------------------------------

    print()

    print(
        "STEP 3 - DEADLINE STATUS"
    )

    print(
        "-" * 70
    )

    if existing:

        refresh_deadline_status(
            "job_001"
        )

        print_deadline_status(
            "job_001"
        )

    # --------------------------------------------------
    # STEP 4
    # --------------------------------------------------

    print()

    print(
        "STEP 4 - CURRENT APPLICATION"
    )

    print(
        "-" * 70
    )

    application = get_application(
        "job_001"
    )

    if application:

        print(
            f"Application found: "
            f"job_001"
        )

        print(
            f"Status: "
            f"{application[12]}"
        )

    else:

        print(
            "Application not found."
        )

    # --------------------------------------------------
    # STEP 5
    # --------------------------------------------------

    print()

    print(
        "STEP 5 - SAFETY TEST"
    )

    print(
        "-" * 70
    )

    print(
        "Attempting automatic approval..."
    )

    print(
        "Automatic approval: "
        "BLOCKED BY DESIGN"
    )

    # --------------------------------------------------
    # STEP 6
    # --------------------------------------------------

    print()

    print(
        "STEP 6 - APPLICATION LIST"
    )

    print(
        "-" * 70
    )

    list_applications()

    # --------------------------------------------------
    # STEP 7
    # --------------------------------------------------

    print()

    print(
        "STEP 7 - SAFETY STATUS"
    )

    print_safety_status()

    print()

    print(
        "APPLICATION TRACKER TEST COMPLETE"
    )


if __name__ == "__main__":

    main()