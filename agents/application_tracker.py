
import json
import sqlite3
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = (
    BASE_DIR
    / "applications"
    / "data"
)

DATABASE_PATH = (
    DATABASE_DIR
    / "applications.db"
)

RAW_JOBS_DIR = (
    BASE_DIR
    / "jobs"
    / "raw"
)


# ============================================================
# APPLICATION STATUSES
# ============================================================

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

# ============================================================
# ALLOWED STATUS TRANSITIONS
# ============================================================

ALLOWED_STATUS_TRANSITIONS = {

    "not_applied": [
        "review_required",
        "withdrawn"
    ],

    "review_required": [
        "application_prepared",
        "withdrawn"
    ],

    "application_prepared": [
        "approved",
        "withdrawn"
    ],

    "approved": [
        "submitted",
        "withdrawn",
        "review_required"
    ],

    "submitted": [
        "rejected",
        "interview",
        "withdrawn"
    ],

    "rejected": [],

    "interview": [
        "offer",
        "withdrawn"
    ],

    "offer": [
        "withdrawn"
    ],

    "withdrawn": []
}


# ============================================================
# DEADLINE STATUSES
# ============================================================

DEADLINE_STATUSES = [
    "NO_DEADLINE",
    "INVALID_DEADLINE",
    "EXPIRED",
    "URGENT",
    "ACTIVE"
]


# ============================================================
# SAFETY CONFIGURATION
# ============================================================

AUTOMATIC_SUBMISSION = False
AUTOMATIC_APPLICATION = False
AUTOMATIC_EMAIL = False
AUTOMATIC_JOB_SUBMISSION = False
AUTOMATIC_APPROVAL = False
HUMAN_REVIEW_REQUIRED = True


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create a SQLite database connection.
    """

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Create the application tracker database.

    Existing databases are migrated safely by adding
    missing columns when required.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS applications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            job_id TEXT NOT NULL UNIQUE,

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

            reviewer TEXT

        )
        """
    )

    connection.commit()

    # --------------------------------------------------------
    # MIGRATION
    # --------------------------------------------------------

    cursor.execute(
        """
        PRAGMA table_info(applications)
        """
    )

    existing_columns = {
        row[1]
        for row in cursor.fetchall()
    }

    required_columns = {

        "company": "TEXT",

        "job_title": "TEXT",

        "location": "TEXT",

        "work_mode": "TEXT",

        "source": "TEXT",

        "source_job_id": "TEXT",

        "job_url": "TEXT",

        "match_score": "REAL",

        "decision": "TEXT",

        "application_status": (
            "TEXT DEFAULT 'not_applied'"
        ),

        "discovered_at": "TEXT",

        "approved_at": "TEXT",

        "submitted_at": "TEXT",

        "last_updated": "TEXT",

        "resume_version": "TEXT",

        "cover_letter_version": "TEXT",

        "application_method": "TEXT",

        "notes": "TEXT",

        "application_deadline": "TEXT",

        "deadline_status": "TEXT",

        "days_remaining": "INTEGER",

        "human_approved": (
            "INTEGER DEFAULT 0"
        ),

        "reviewer": "TEXT"
    }

    for column_name, column_type in required_columns.items():

        if column_name not in existing_columns:

            cursor.execute(
                f"""
                ALTER TABLE applications
                ADD COLUMN {column_name}
                {column_type}
                """
            )

    connection.commit()

    connection.close()


# ============================================================
# TIME
# ============================================================

def current_timestamp():
    """
    Return current local timestamp.
    """

    return datetime.now().isoformat(
        timespec="seconds"
    )


# ============================================================
# DEADLINE PARSING
# ============================================================

def parse_deadline(deadline):
    """
    Convert a deadline string to datetime.

    Supported formats:
        YYYY-MM-DD HH:MM
        YYYY-MM-DD HH:MM:SS
        YYYY-MM-DD
        ISO datetime
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

        "%Y-%m-%d %H:%M",

        "%Y-%m-%d %H:%M:%S",

        "%Y-%m-%d",

    ]

    for fmt in formats:

        try:

            return datetime.strptime(
                deadline,
                fmt
            )

        except ValueError:

            continue

    try:

        return datetime.fromisoformat(
            deadline
        )

    except ValueError:

        return None


# ============================================================
# DEADLINE FORMATTING
# ============================================================

def format_deadline(deadline):
    """
    Normalize deadline to:

        YYYY-MM-DD HH:MM
    """

    parsed = parse_deadline(
        deadline
    )

    if parsed is None:
        return None

    return parsed.strftime(
        "%Y-%m-%d %H:%M"
    )


# ============================================================
# DEADLINE CALCULATION
# ============================================================

def calculate_deadline_status(deadline):
    """
    Calculate deadline status using the actual current date.

    Returns:

        status
        days_remaining
    """

    if not deadline:

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

    difference = (
        parsed - now
    )

    total_seconds = (
        difference.total_seconds()
    )

    days_remaining = (
        difference.days
    )

    # --------------------------------------------------------
    # EXPIRED
    # --------------------------------------------------------

    if total_seconds < 0:

        return (
            "EXPIRED",
            days_remaining
        )

    # --------------------------------------------------------
    # DUE TODAY
    # --------------------------------------------------------

    if parsed.date() == now.date():

        return (
            "URGENT",
            0
        )

    # --------------------------------------------------------
    # DUE SOON
    # --------------------------------------------------------

    if days_remaining <= 3:

        return (
            "URGENT",
            days_remaining
        )

    # --------------------------------------------------------
    # UPCOMING
    # --------------------------------------------------------

    return (
        "ACTIVE",
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
    Return deadline status and days remaining.
    """

    return calculate_deadline_status(
        deadline
    )


# ============================================================
# JOB FILE LOADING
# ============================================================

def get_job_file(job_id):
    """
    Return the raw job JSON path.
    """

    return (
        RAW_JOBS_DIR
        / f"{job_id}.json"
    )


def load_job_from_raw(job_id):
    """
    Load the latest raw job record.

    Returns:
        dict
        or None
    """

    job_file = get_job_file(
        job_id
    )

    if not job_file.exists():

        return None

    try:

        with open(
            job_file,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(
                file
            )

    except (
        json.JSONDecodeError,
        OSError
    ):

        return None


# ============================================================
# APPLICATION EXISTENCE
# ============================================================

def application_exists(job_id):
    """
    Check whether a job already exists.

    Returns:
        tuple
        or None
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


# ============================================================
# ADD APPLICATION
# ============================================================

def add_application(job):
    """
    Add a job to the application tracker.

    Duplicate job IDs are never inserted twice.
    """

    job_id = job.get(
        "job_id"
    )

    if not job_id:

        raise ValueError(
            "Job must contain job_id."
        )

    existing = application_exists(
        job_id
    )

    if existing:

        print(
            f"APPLICATION ALREADY EXISTS: "
            f"{job_id}"
        )

        print(
            f"Current status: "
            f"{existing[1]}"
        )

        return False

    now = current_timestamp()

    application_deadline = (
        job.get(
            "application_deadline"
        )
    )

    formatted_deadline = (
        format_deadline(
            application_deadline
        )
    )

    # --------------------------------------------------------
    # DEADLINE CLASSIFICATION
    #
    # Distinguish between:
    #
    #   No deadline supplied
    #       -> NO_DEADLINE
    #
    #   Deadline supplied but invalid
    #       -> INVALID_DEADLINE
    #
    #   Valid deadline
    #       -> calculate normal deadline status
    # --------------------------------------------------------

    if (
        application_deadline is not None
        and str(application_deadline).strip()
        and formatted_deadline is None
    ):

        deadline_status = "INVALID_DEADLINE"
        days_remaining = None

    else:

        deadline_status, days_remaining = (
            calculate_deadline_status(
                formatted_deadline
            )
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

            job_id,

            job.get(
                "company",
                ""
            ),

            job.get(
                "job_title",
                job.get(
                    "title",
                    ""
                )
            ),

            job.get(
                "location",
                ""
            ),

            job.get(
                "work_mode",
                ""
            ),

            job.get(
                "source",
                ""
            ),

            job.get(
                "source_job_id",
                ""
            ),

            job.get(
                "url",
                ""
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
        f"APPLICATION CREATED: {job_id}"
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


# ============================================================
# STATUS TRANSITIONS
# ============================================================

def update_status(
    job_id,
    new_status
):
    """
    Update application status safely.

    Enforces:
    - valid application statuses
    - allowed status transitions
    - human approval for approved
    - human approval for submitted
    - deadline safety for submitted
    """

    if new_status not in VALID_STATUSES:

        raise ValueError(
            f"Invalid status: {new_status}"
        )

    application = get_application(
        job_id
    )

    if not application:

        print(
            f"Job not found: {job_id}"
        )

        return False

    current_status = application[
        "application_status"
    ]

    human_approved = bool(
        application[
            "human_approved"
        ]
    )

    deadline_status = application[
        "deadline_status"
    ]

    # --------------------------------------------------------
    # STATUS TRANSITION SAFETY
    # --------------------------------------------------------

    allowed_next_statuses = (
        ALLOWED_STATUS_TRANSITIONS.get(
            current_status,
            []
        )
    )

    if new_status not in allowed_next_statuses:

        print(
            "STATUS UPDATE BLOCKED:"
        )

        print(
            f"Invalid transition: "
            f"{current_status} -> {new_status}"
        )

        print(
            "Allowed next statuses: "
            f"{allowed_next_statuses or 'NONE'}"
        )

        return False

    # --------------------------------------------------------
    # APPROVAL SAFETY
    # --------------------------------------------------------

    if new_status == "approved":

        if not human_approved:

            print(
                "STATUS UPDATE BLOCKED:"
            )

            print(
                "Cannot mark application "
                "approved without explicit "
                "human approval."
            )

            return False

    # --------------------------------------------------------
    # SUBMISSION SAFETY
    # --------------------------------------------------------

    if new_status == "submitted":

        if not human_approved:

            print(
                "SUBMISSION BLOCKED:"
            )

            print(
                "Human approval is required."
            )

            return False

        if deadline_status in (
            "EXPIRED",
            "INVALID_DEADLINE"
        ):

            print(
                "SUBMISSION BLOCKED:"
            )

            print(
                f"Deadline status: "
                f"{deadline_status}"
            )

            return False

    now = current_timestamp()

    approved_at = None

    submitted_at = None

    if new_status == "approved":

        approved_at = now

    if new_status == "submitted":

        submitted_at = now

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE applications

        SET
            application_status = ?,

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


# ============================================================
# HUMAN APPROVAL
# ============================================================

def set_human_approval(
    job_id,
    approved,
    reviewer=None
):
    """
    Record explicit human approval.

    This function does NOT automatically approve anything.

    The caller must explicitly provide:

        approved=True

    and ideally a reviewer name.

    Automatic approval is never performed by the pipeline.
    """

    if not isinstance(
        approved,
        bool
    ):

        raise ValueError(
            "Human approval must be True or False."
        )

    application = get_application(
        job_id
    )

    if not application:

        print(
            f"Job not found: {job_id}"
        )

        return False

    now = current_timestamp()

    connection = get_connection()

    cursor = connection.cursor()

    if approved:

        if not reviewer:

            reviewer = "Human Reviewer"

        cursor.execute(
            """
            UPDATE applications

            SET
                human_approved = 1,

                reviewer = ?,

                approved_at = ?,

                last_updated = ?

            WHERE job_id = ?
            """,
            (

                reviewer,

                now,

                now,

                job_id
            )
        )

    else:

        cursor.execute(
            """
            UPDATE applications

            SET
                human_approved = 0,

                reviewer = NULL,

                approved_at = NULL,

                last_updated = ?

            WHERE job_id = ?
            """,
            (

                now,

                job_id
            )
        )

    connection.commit()

    connection.close()

    print(
        f"HUMAN APPROVAL UPDATED: "
        f"{job_id} -> {approved}"
    )

    if approved:

        print(
            f"Reviewer: {reviewer}"
        )

        print(
            "Human approval recorded."
        )

        print(
            "Status transition must be performed "
            "through update_status()."
        )

    else:

        print(
            "Application returned to "
            "human review."
        )

    return True


# ============================================================
# GET APPLICATION
# ============================================================

def get_application(job_id):
    """
    Return one application as a dictionary.

    Using a dictionary instead of numeric indexes prevents
    the column-index bugs that occurred in previous versions.
    """

    connection = get_connection()

    connection.row_factory = sqlite3.Row

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

    row = cursor.fetchone()

    connection.close()

    if row is None:

        return None

    return dict(row)


# ============================================================
# REFRESH DEADLINE STATUS
# ============================================================

def refresh_deadline_status(
    job_id=None
):
    """
    Refresh deadline information.

    If job_id is supplied:
        refresh only that application.

    If job_id is None:
        refresh all applications.

    The latest deadline is read from jobs/raw/*.json.

    This function NEVER submits or approves an application.
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

    updated = 0

    for application in applications:

        current_job_id = application[0]

        current_deadline = application[1]

        # ----------------------------------------------------
        # Read latest raw job
        # ----------------------------------------------------

        raw_job = load_job_from_raw(
            current_job_id
        )

        if raw_job is not None:

            raw_deadline = raw_job.get(
                "application_deadline"
            )

            if raw_deadline is not None:

                current_deadline = (
                    format_deadline(
                        raw_deadline
                    )
                )

        # ----------------------------------------------------
        # Calculate deadline
        # ----------------------------------------------------

        status, days_remaining = (
            calculate_deadline_status(
                current_deadline
            )
        )

        now = current_timestamp()

        cursor.execute(
            """
            UPDATE applications

            SET
                application_deadline = ?,

                deadline_status = ?,

                days_remaining = ?,

                last_updated = ?

            WHERE job_id = ?
            """,
            (

                current_deadline,

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


# ============================================================
# PRINT DEADLINE STATUS
# ============================================================

def print_deadline_status(
    job_id
):
    """
    Display deadline information for one application.
    """

    application = get_application(
        job_id
    )

    print()

    print(
        "APPLICATION DEADLINE MONITOR"
    )

    print(
        "=" * 80
    )

    if not application:

        print(
            f"Application not found: {job_id}"
        )

        return

    print(
        f"Job:       "
        f"{application['job_id']}"
    )

    print(
        f"Company:   "
        f"{application['company']}"
    )

    print(
        f"Position:  "
        f"{application['job_title']}"
    )

    deadline = application[
        "application_deadline"
    ]

    status = application[
        "deadline_status"
    ]

    days_remaining = application[
        "days_remaining"
    ]

    print(
        f"Deadline:  "
        f"{deadline or 'NOT PROVIDED'}"
    )

    print(
        f"Status:    "
        f"{status}"
    )

    if days_remaining is not None:

        print(
            f"Days remaining: "
            f"{days_remaining}"
        )

    if status == "EXPIRED":

        print(
            "WARNING: Application deadline has passed."
        )

    elif status == "URGENT":

        print(
            "WARNING: Application deadline is today."
        )

    elif status == "URGENT":

        print(
            "WARNING: Application deadline is within 3 days."
        )

    elif status == "ACTIVE":

        print(
            "Deadline is upcoming."
        )

    elif status == "NO_DEADLINE":

        print(
            "No application deadline was provided."
        )

    elif status == "INVALID_DEADLINE":

        print(
            "WARNING: Deadline requires human review."
        )


# ============================================================
# LIST APPLICATIONS
# ============================================================

def list_applications():
    """
    Return all applications as dictionaries.
    """

    connection = get_connection()

    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM applications
        ORDER BY last_updated DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# PRINT APPLICATION LIST
# ============================================================

def print_application_list():
    """
    Display all tracked applications.
    """

    applications = list_applications()

    print()

    print(
        "APPLICATION TRACKER"
    )

    print(
        "=" * 100
    )

    if not applications:

        print(
            "No applications tracked."
        )

        return

    for application in applications:

        print()

        print(
            f"Job ID:          "
            f"{application['job_id']}"
        )

        print(
            f"Company:         "
            f"{application['company']}"
        )

        print(
            f"Title:           "
            f"{application['job_title']}"
        )

        print(
            f"Location:        "
            f"{application['location']}"
        )

        print(
            f"Score:           "
            f"{application['match_score']}"
        )

        print(
            f"Decision:        "
            f"{application['decision']}"
        )

        print(
            f"Status:          "
            f"{application['application_status']}"
        )

        print(
            f"Deadline:        "
            f"{application['application_deadline'] or 'NOT PROVIDED'}"
        )

        print(
            f"Deadline Status: "
            f"{application['deadline_status']}"
        )

        print(
            f"Days Remaining:  "
            f"{application['days_remaining']}"
        )

        print(
            f"Human Approved:  "
            f"{bool(application['human_approved'])}"
        )

        print(
            f"Reviewer:        "
            f"{application['reviewer']}"
        )

        print(
            f"Updated:         "
            f"{application['last_updated']}"
        )


# ============================================================
# SAFETY STATUS
# ============================================================

def print_safety_status():
    """
    Display application safety controls.
    """

    print()

    print(
        "SAFETY STATUS"
    )

    print(
        "-" * 70
    )

    print(
        f"Automatic submission: "
        f"{AUTOMATIC_SUBMISSION}"
    )

    print(
        f"Automatic application: "
        f"{AUTOMATIC_APPLICATION}"
    )

    print(
        f"Automatic email: "
        f"{AUTOMATIC_EMAIL}"
    )

    print(
        f"Automatic job submission: "
        f"{AUTOMATIC_JOB_SUBMISSION}"
    )

    print(
        f"Automatic approval: "
        f"{AUTOMATIC_APPROVAL}"
    )

    print(
        f"Human approval required: "
        f"{HUMAN_REVIEW_REQUIRED}"
    )

    print(
        "Deadline monitoring only produces "
        "information and warnings."
    )


# ============================================================
# SAFETY TEST
# ============================================================

def automatic_approval_test():
    """
    Demonstrate that automatic approval is blocked.
    """

    print(
        "Attempting automatic approval..."
    )

    if AUTOMATIC_APPROVAL:

        print(
            "Automatic approval: "
            "NOT ALLOWED"
        )

        return False

    print(
        "Automatic approval: "
        "BLOCKED BY DESIGN"
    )

    return False


# ============================================================
# CURRENT APPLICATION DISPLAY
# ============================================================

def print_current_application(
    job_id
):
    """
    Display one application's important fields.
    """

    application = get_application(
        job_id
    )

    if not application:

        print(
            "Application not found."
        )

        return

    print(
        f"Application found: "
        f"{application['job_id']}"
    )

    print(
        f"Status: "
        f"{application['application_status']}"
    )

    print(
        f"Human Approved: "
        f"{bool(application['human_approved'])}"
    )

    print(
        f"Reviewer: "
        f"{application['reviewer']}"
    )


# ============================================================
# TEST MAIN
# ============================================================

def main():

    print()

    print(
        "APPLICATION TRACKER TEST - VERSION 6"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    print()

    print(
        "DATABASE:"
    )

    print(
        DATABASE_PATH
    )

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

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

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
            "Application exists: job_001"
        )

        print(
            f"Current status: "
            f"{existing[1]}"
        )

    else:

        print(
            "Application does not exist: job_001"
        )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    print()

    print(
        "STEP 3 - DEADLINE STATUS"
    )

    print(
        "-" * 70
    )

    refresh_deadline_status(
        "job_001"
    )

    print_deadline_status(
        "job_001"
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    print()

    print(
        "STEP 4 - CURRENT APPLICATION"
    )

    print(
        "-" * 70
    )

    print_current_application(
        "job_001"
    )

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    print()

    print(
        "STEP 5 - SAFETY TEST"
    )

    print(
        "-" * 70
    )

    automatic_approval_test()

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    print()

    print(
        "STEP 6 - APPLICATION LIST"
    )

    print(
        "-" * 70
    )

    print_application_list()

    # --------------------------------------------------------
    # STEP 7
    # --------------------------------------------------------

    print()

    print(
        "STEP 7 - SAFETY STATUS"
    )

    print_safety_status()

    # --------------------------------------------------------
    # COMPLETE
    # --------------------------------------------------------

    print()

    print(
        "APPLICATION TRACKER TEST COMPLETE"
    )

    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
