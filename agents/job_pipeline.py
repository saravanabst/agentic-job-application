import json
from pathlib import Path
from datetime import datetime

from job_loader import (
    load_all_jobs,
    validate_job,
    get_application_deadline
)

from duplicate_detector import find_duplicates

from application_tracker import (
    initialize_database,
    application_exists,
    add_application,
    get_application,
    get_deadline_status
)


BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DEADLINE STATUS NORMALIZATION
# ============================================================

def normalize_deadline_status(
    deadline_status,
    application_deadline
):
    """
    Normalize the deadline status returned by the tracker.

    The tracker may return INVALID_DEADLINE when the
    deadline value is empty or missing.

    For this pipeline:

        No deadline provided
            -> NO_DEADLINE

        Valid deadline
            -> use tracker status

    We do not invent or modify deadline dates.
    """

    if not application_deadline:

        return "NO_DEADLINE"

    if not deadline_status:

        return "NO_DEADLINE"

    if (
        deadline_status == "INVALID_DEADLINE"
        and not application_deadline
    ):

        return "NO_DEADLINE"

    return deadline_status


# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(job):
    """
    Process one valid job through the application
    tracking layer.

    The application deadline is passed from the job
    record into the application tracker.
    """

    job_id = job.get(
        "job_id"
    )

    company = job.get(
        "company",
        ""
    )

    title = job.get(
        "title",
        ""
    )

    print()

    print(
        f"Processing: "
        f"{job_id} - "
        f"{company} - "
        f"{title}"
    )

    # --------------------------------------------------------
    # APPLICATION DEADLINE
    # --------------------------------------------------------

    application_deadline = get_application_deadline(
        job
    )

    if application_deadline:

        print(
            f"  Application deadline: "
            f"{application_deadline}"
        )

    else:

        print(
            "  Application deadline: "
            "NOT PROVIDED"
        )

    # --------------------------------------------------------
    # CHECK EXISTING APPLICATION
    # --------------------------------------------------------

    existing = application_exists(
        job_id
    )

    if existing:

        print(
            "  SKIPPED: already tracked"
        )

        print(
            f"  Existing status: "
            f"{existing[1]}"
        )

        return "already_tracked"

    # --------------------------------------------------------
    # MATCH SCORE
    # --------------------------------------------------------

    match_score = job.get(
        "match_score"
    )

    if match_score is None:

        match_score = 0

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    decision = job.get(
        "decision"
    )

    if not decision:

        decision = "REVIEW"

    # --------------------------------------------------------
    # APPLICATION RECORD
    # --------------------------------------------------------

    application_record = {

        "job_id":
            job_id,

        "company":
            company,

        "title":
            title,

        "location":
            job.get(
                "location",
                ""
            ),

        "work_mode":
            job.get(
                "work_mode",
                ""
            ),

        "source":
            job.get(
                "source",
                ""
            ),

        "source_job_id":
            job.get(
                "source_job_id",
                ""
            ),

        "url":
            job.get(
                "url",
                ""
            ),

        "match_score":
            match_score,

        "decision":
            decision,

        "application_deadline":
            application_deadline,

        "discovered_at":
            job.get(
                "discovered_at",
                ""
            ),

        "notes":
            job.get(
                "notes",
                ""
            )
    }

    # --------------------------------------------------------
    # ADD APPLICATION
    # --------------------------------------------------------

    created = add_application(
        application_record
    )

    if not created:

        return "already_tracked"

    return "tracked"


# ============================================================
# PRINT DEADLINE SUMMARY
# ============================================================

def print_deadline_summary(
    job_id,
    job
):
    """
    Display deadline information for a tracked
    application.

    The tracker remains the source of truth for
    deadline status.

    Missing deadline is displayed as NO_DEADLINE.
    """

    application = get_application(
        job_id
    )

    if not application:

        print(
            "  Deadline status unavailable:"
            " application not found."
        )

        return

    # --------------------------------------------------------
    # Get deadline directly from the current job record
    # --------------------------------------------------------

    application_deadline = get_application_deadline(
        job
    )

    # --------------------------------------------------------
    # Ask tracker for current deadline status
    # --------------------------------------------------------

    try:

        raw_status = get_deadline_status(
            job_id
        )

    except Exception as error:

        print(
            "  Deadline monitoring error:"
        )

        print(
            f"  {error}"
        )

        return

    # --------------------------------------------------------
    # Normalize status
    # --------------------------------------------------------

    deadline_status = normalize_deadline_status(
        raw_status,
        application_deadline
    )

    # --------------------------------------------------------
    # Display deadline
    # --------------------------------------------------------

    if application_deadline:

        print(
            f"  Deadline: "
            f"{application_deadline}"
        )

    else:

        print(
            "  Deadline: "
            "NOT PROVIDED"
        )

    # --------------------------------------------------------
    # Display status
    # --------------------------------------------------------

    print(
        f"  Deadline status: "
        f"{deadline_status}"
    )

    # --------------------------------------------------------
    # Days remaining
    #
    # Only calculate when a valid deadline exists.
    # We do not calculate anything for NO_DEADLINE.
    # --------------------------------------------------------

    if not application_deadline:

        return

    # --------------------------------------------------------
    # Try to calculate days remaining locally.
    #
    # Supported formats:
    #
    # YYYY-MM-DD
    # YYYY-MM-DD HH:MM
    # YYYY-MM-DD HH:MM:SS
    # --------------------------------------------------------

    deadline_datetime = None

    deadline_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d"
    ]

    for deadline_format in deadline_formats:

        try:

            deadline_datetime = datetime.strptime(
                str(application_deadline),
                deadline_format
            )

            break

        except ValueError:

            continue

    if deadline_datetime is None:

        return

    now = datetime.now()

    difference = (
        deadline_datetime - now
    )

    days_remaining = difference.days

    # --------------------------------------------------------
    # For a future deadline, display days remaining.
    # For an expired deadline, display negative days.
    # --------------------------------------------------------

    print(
        f"  Days remaining: "
        f"{days_remaining}"
    )


# ============================================================
# DEADLINE MONITORING
# ============================================================

def process_deadline_monitoring(
    jobs
):
    """
    Monitor deadlines for tracked applications.

    This function is informational only.

    It NEVER:

        - submits applications
        - approves applications
        - sends emails
        - submits jobs automatically
    """

    print()

    print(
        "STEP 6: Deadline monitoring..."
    )

    if not jobs:

        print(
            "No jobs available for "
            "deadline monitoring."
        )

        return

    monitored = 0

    for job in jobs:

        job_id = job.get(
            "job_id"
        )

        if not job_id:

            continue

        existing = application_exists(
            job_id
        )

        if not existing:

            continue

        print()

        print(
            f"Deadline check: "
            f"{job_id}"
        )

        print_deadline_summary(
            job_id,
            job
        )

        monitored += 1

    if monitored == 0:

        print(
            "No tracked applications "
            "available for deadline monitoring."
        )

    print()

    print(
        "Deadline monitoring is "
        "informational only."
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()

    print(
        "AGENTIC JOB APPLICATION PIPELINE"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # STEP 1 — DATABASE
    # ========================================================

    print()

    print(
        "STEP 1: Initializing "
        "application database..."
    )

    initialize_database()

    print(
        "Database ready."
    )

    # ========================================================
    # STEP 2 — LOAD JOBS
    # ========================================================

    print()

    print(
        "STEP 2: Loading jobs..."
    )

    jobs = load_all_jobs()

    print(
        f"Jobs loaded: "
        f"{len(jobs)}"
    )

    if not jobs:

        print(
            "No jobs found."
        )

        return

    # ========================================================
    # STEP 3 — VALIDATE JOBS
    # ========================================================

    print()

    print(
        "STEP 3: Validating jobs..."
    )

    valid_jobs = []

    for job in jobs:

        missing_fields = validate_job(
            job
        )

        if missing_fields:

            print()

            print(
                f"INVALID JOB: "
                f"{job.get('job_id', 'UNKNOWN')}"
            )

            print(
                f"Missing fields: "
                f"{', '.join(missing_fields)}"
            )

            continue

        valid_jobs.append(
            job
        )

    print(
        f"Valid jobs: "
        f"{len(valid_jobs)}/{len(jobs)}"
    )

    # ========================================================
    # STEP 4 — DUPLICATE DETECTION
    # ========================================================

    print()

    print(
        "STEP 4: Checking duplicates..."
    )

    duplicates = find_duplicates(
        valid_jobs
    )

    duplicate_ids = {
        duplicate["job_id"]
        for duplicate in duplicates
    }

    print(
        f"Duplicates found: "
        f"{len(duplicates)}"
    )

    for duplicate in duplicates:

        print(
            f"  {duplicate['job_id']} "
            f"is duplicate of "
            f"{duplicate['duplicate_of']} "
            f"({duplicate['match_type']})"
        )

    # ========================================================
    # STEP 5 — APPLICATION TRACKING
    # ========================================================

    print()

    print(
        "STEP 5: Application tracking..."
    )

    results = {
        "tracked": 0,
        "already_tracked": 0,
        "duplicates": 0
    }

    for job in valid_jobs:

        job_id = job.get(
            "job_id"
        )

        if job_id in duplicate_ids:

            print()

            print(
                f"SKIPPED DUPLICATE: "
                f"{job_id}"
            )

            results[
                "duplicates"
            ] += 1

            continue

        result = process_job(
            job
        )

        if result in results:

            results[
                result
            ] += 1

    # ========================================================
    # STEP 6 — DEADLINE MONITORING
    # ========================================================

    process_deadline_monitoring(
        valid_jobs
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()

    print(
        "=" * 70
    )

    print(
        "PIPELINE COMPLETE"
    )

    print(
        "=" * 70
    )

    print(
        f"Jobs loaded:       "
        f"{len(jobs)}"
    )

    print(
        f"Valid jobs:        "
        f"{len(valid_jobs)}"
    )

    print(
        f"Duplicates:        "
        f"{results['duplicates']}"
    )

    print(
        f"Newly tracked:     "
        f"{results['tracked']}"
    )

    print(
        f"Already tracked:   "
        f"{results['already_tracked']}"
    )

    # ========================================================
    # SAFETY STATUS
    # ========================================================

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

    print()

    print(
        f"Completed at:      "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":

    main()