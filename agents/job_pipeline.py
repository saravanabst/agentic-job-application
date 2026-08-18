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
# DEADLINE HELPERS
# ============================================================

def normalize_deadline_status(
    deadline_status,
    application_deadline
):
    """
    Normalize deadline status.

    If no deadline was supplied, the correct status is
    NO_DEADLINE rather than INVALID_DEADLINE.
    """

    if not application_deadline:
        return "NO_DEADLINE"

    if not deadline_status:
        return "NO_DEADLINE"

    return deadline_status


def get_deadline_information(job):
    """
    Return deadline information for a job.

    Returns:

        {
            "deadline": value,
            "status": status,
            "days_remaining": value
        }
    """

    application_deadline = get_application_deadline(
        job
    )

    # --------------------------------------------------------
    # No deadline
    # --------------------------------------------------------

    if not application_deadline:

        return {
            "deadline": None,
            "status": "NO_DEADLINE",
            "days_remaining": None
        }

    # --------------------------------------------------------
    # Ask tracker for the current status
    # --------------------------------------------------------

    job_id = job.get(
        "job_id"
    )

    try:

        deadline_status = get_deadline_status(
            job_id
        )

    except Exception:

        deadline_status = None

    deadline_status = normalize_deadline_status(
        deadline_status,
        application_deadline
    )

    # --------------------------------------------------------
    # Calculate days remaining
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

    days_remaining = None

    if deadline_datetime:

        difference = (
            deadline_datetime - datetime.now()
        )

        days_remaining = difference.days

        # ----------------------------------------------------
        # If the date is actually in the past but tracker
        # returned another status, enforce EXPIRED here.
        # ----------------------------------------------------

        if difference.total_seconds() < 0:

            deadline_status = "EXPIRED"

    return {
        "deadline": application_deadline,
        "status": deadline_status,
        "days_remaining": days_remaining
    }


def print_deadline_information(
    job,
    deadline_info
):
    """
    Display deadline information.
    """

    job_id = job.get(
        "job_id"
    )

    print()

    print(
        f"Deadline check: {job_id}"
    )

    deadline = deadline_info.get(
        "deadline"
    )

    status = deadline_info.get(
        "status"
    )

    days_remaining = deadline_info.get(
        "days_remaining"
    )

    if deadline:

        print(
            f"  Deadline: {deadline}"
        )

    else:

        print(
            "  Deadline: NOT PROVIDED"
        )

    print(
        f"  Deadline status: {status}"
    )

    if days_remaining is not None:

        print(
            f"  Days remaining: {days_remaining}"
        )

    # --------------------------------------------------------
    # Human-readable priority warning
    # --------------------------------------------------------

    if status == "EXPIRED":

        print(
            "  ACTION: SKIP - APPLICATION DEADLINE EXPIRED"
        )

    elif status == "URGENT":

        print(
            "  ACTION: URGENT - DEADLINE IS VERY CLOSE"
        )

    elif (
        days_remaining is not None
        and days_remaining <= 1
        and days_remaining >= 0
    ):

        print(
            "  ACTION: URGENT - DEADLINE IS WITHIN 24 HOURS"
        )

    elif (
        days_remaining is not None
        and days_remaining <= 3
        and days_remaining >= 0
    ):

        print(
            "  ACTION: HIGH PRIORITY - DEADLINE IS WITHIN 3 DAYS"
        )

    elif status == "NO_DEADLINE":

        print(
            "  WARNING: No application deadline was provided."
        )


def deadline_allows_processing(
    deadline_info
):
    """
    Determine whether the job can continue through
    the application pipeline.

    Expired jobs are stopped.

    Jobs without a deadline are allowed to continue,
    but remain flagged as NO_DEADLINE.
    """

    status = deadline_info.get(
        "status"
    )

    if status == "EXPIRED":

        return False

    return True


# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(job):
    """
    Process one valid job.

    Deadline checking happens BEFORE duplicate checking
    and application tracking.
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

    # ========================================================
    # STEP A — DEADLINE CHECK
    # ========================================================

    deadline_info = get_deadline_information(
        job
    )

    print_deadline_information(
        job,
        deadline_info
    )

    # --------------------------------------------------------
    # Stop immediately if deadline has expired.
    # --------------------------------------------------------

    if not deadline_allows_processing(
        deadline_info
    ):

        print()

        print(
            "  SKIPPED: application deadline has expired."
        )

        return "deadline_expired"

    # ========================================================
    # STEP B — DUPLICATE CHECK
    # ========================================================

    existing = application_exists(
        job_id
    )

    if existing:

        print()

        print(
            "  SKIPPED: already tracked"
        )

        print(
            f"  Existing status: "
            f"{existing[1]}"
        )

        return "already_tracked"

    # ========================================================
    # STEP C — MATCH SCORE
    # ========================================================

    match_score = job.get(
        "match_score"
    )

    if match_score is None:

        match_score = 0

    # ========================================================
    # STEP D — DECISION
    # ========================================================

    decision = job.get(
        "decision"
    )

    if not decision:

        decision = "REVIEW"

    # ========================================================
    # STEP E — CREATE APPLICATION RECORD
    # ========================================================

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
            deadline_info.get(
                "deadline"
            ),

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

    # ========================================================
    # STEP F — ADD TO TRACKER
    # ========================================================

    created = add_application(
        application_record
    )

    if not created:

        return "already_tracked"

    return "tracked"


# ============================================================
# DEADLINE MONITORING
# ============================================================

def process_deadline_monitoring(
    jobs
):
    """
    Perform informational deadline monitoring.

    This does NOT approve, submit, email, or apply.
    """

    print()

    print(
        "STEP 6: Deadline monitoring..."
    )

    if not jobs:

        print(
            "No jobs available for deadline monitoring."
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

        deadline_info = get_deadline_information(
            job
        )

        print()

        print(
            f"Tracked deadline: {job_id}"
        )

        print_deadline_information(
            job,
            deadline_info
        )

        monitored += 1

    if monitored == 0:

        print(
            "No tracked applications available "
            "for deadline monitoring."
        )

    print()

    print(
        "Deadline monitoring is informational only."
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    print()

    print(
        "AGENTIC JOB APPLICATION PIPELINE - VERSION 6"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # STEP 1 — DATABASE
    # ========================================================

    print()

    print(
        "STEP 1: Initializing application database..."
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
        f"Jobs loaded: {len(jobs)}"
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
    # STEP 4 — EARLY DEADLINE SCREENING
    # ========================================================

    print()

    print(
        "STEP 4: Checking application deadlines..."
    )

    deadline_results = {
        "no_deadline": 0,
        "active": 0,
        "expired": 0
    }

    deadline_valid_jobs = []

    for job in valid_jobs:

        deadline_info = get_deadline_information(
            job
        )

        print_deadline_information(
            job,
            deadline_info
        )

        status = deadline_info.get(
            "status"
        )

        if status == "EXPIRED":

            deadline_results[
                "expired"
            ] += 1

            print(
                "  Job removed from further processing."
            )

            continue

        if status == "NO_DEADLINE":

            deadline_results[
                "no_deadline"
            ] += 1

        else:

            deadline_results[
                "active"
            ] += 1

        deadline_valid_jobs.append(
            job
        )

    print()

    print(
        "DEADLINE SCREENING SUMMARY"
    )

    print(
        f"  No deadline: "
        f"{deadline_results['no_deadline']}"
    )

    print(
        f"  Active deadline: "
        f"{deadline_results['active']}"
    )

    print(
        f"  Expired: "
        f"{deadline_results['expired']}"
    )

    print(
        f"  Jobs continuing: "
        f"{len(deadline_valid_jobs)}"
    )

    # ========================================================
    # STEP 5 — DUPLICATE DETECTION
    # ========================================================

    print()

    print(
        "STEP 5: Checking duplicates..."
    )

    duplicates = find_duplicates(
        deadline_valid_jobs
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
    # STEP 6 — APPLICATION TRACKING
    # ========================================================

    print()

    print(
        "STEP 6: Application tracking..."
    )

    results = {
        "tracked": 0,
        "already_tracked": 0,
        "duplicates": 0,
        "deadline_expired": deadline_results[
            "expired"
        ]
    }

    for job in deadline_valid_jobs:

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
    # STEP 7 — INFORMATIONAL DEADLINE MONITORING
    # ========================================================

    print()

    print(
        "STEP 7: Deadline monitoring..."
    )

    tracked_jobs = []

    for job in deadline_valid_jobs:

        job_id = job.get(
            "job_id"
        )

        if application_exists(
            job_id
        ):

            tracked_jobs.append(
                job
            )

    process_deadline_monitoring(
        tracked_jobs
    )

    # ========================================================
    # PIPELINE SUMMARY
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
        f"Jobs loaded:        "
        f"{len(jobs)}"
    )

    print(
        f"Valid jobs:         "
        f"{len(valid_jobs)}"
    )

    print(
        f"Expired jobs:       "
        f"{results['deadline_expired']}"
    )

    print(
        f"Deadline-cleared:   "
        f"{len(deadline_valid_jobs)}"
    )

    print(
        f"Duplicates:         "
        f"{results['duplicates']}"
    )

    print(
        f"Newly tracked:      "
        f"{results['tracked']}"
    )

    print(
        f"Already tracked:    "
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
        "Deadline monitoring is informational only."
    )

    print()

    print(
        f"Completed at: "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":

    main()
