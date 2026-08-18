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
    add_application
)


BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# DEADLINE HELPERS
# ============================================================

DEADLINE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d"
]


def parse_deadline(deadline):
    """
    Convert an application deadline into a datetime.

    Supported formats:

        YYYY-MM-DD HH:MM:SS
        YYYY-MM-DD HH:MM
        YYYY-MM-DD

    Returns:
        datetime object when valid
        None when empty or invalid
    """

    if deadline is None:
        return None

    deadline_text = str(
        deadline
    ).strip()

    if not deadline_text:
        return None

    for deadline_format in DEADLINE_FORMATS:

        try:

            return datetime.strptime(
                deadline_text,
                deadline_format
            )

        except ValueError:

            continue

    return None


def get_deadline_information(job):
    """
    Determine the application deadline status directly
    from the discovered job record.

    Possible statuses:

        NO_DEADLINE
        ACTIVE
        URGENT
        EXPIRED
        INVALID_DEADLINE
    """

    application_deadline = get_application_deadline(
        job
    )

    # --------------------------------------------------------
    # NO DEADLINE
    # --------------------------------------------------------

    if not application_deadline:

        return {
            "deadline": None,
            "status": "NO_DEADLINE",
            "days_remaining": None
        }

    # --------------------------------------------------------
    # PARSE DEADLINE
    # --------------------------------------------------------

    deadline_datetime = parse_deadline(
        application_deadline
    )

    if deadline_datetime is None:

        return {
            "deadline": application_deadline,
            "status": "INVALID_DEADLINE",
            "days_remaining": None
        }

    # --------------------------------------------------------
    # CALCULATE TIME REMAINING
    # --------------------------------------------------------

    now = datetime.now()

    difference = (
        deadline_datetime - now
    )

    days_remaining = difference.days

    # --------------------------------------------------------
    # EXPIRED
    # --------------------------------------------------------

    if difference.total_seconds() < 0:

        return {
            "deadline": application_deadline,
            "status": "EXPIRED",
            "days_remaining": days_remaining
        }

    # --------------------------------------------------------
    # URGENT
    # --------------------------------------------------------

    if difference.total_seconds() <= 48 * 60 * 60:

        return {
            "deadline": application_deadline,
            "status": "URGENT",
            "days_remaining": days_remaining
        }

    # --------------------------------------------------------
    # ACTIVE
    # --------------------------------------------------------

    return {
        "deadline": application_deadline,
        "status": "ACTIVE",
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
    # HUMAN-READABLE ACTION
    # --------------------------------------------------------

    if status == "EXPIRED":

        print(
            "  ACTION: SKIP EXPIRED JOB"
        )

    elif status == "URGENT":

        print(
            "  ACTION: URGENT DEADLINE"
        )

    elif status == "ACTIVE":

        print(
            "  ACTION: CONTINUE PROCESSING"
        )

    elif status == "NO_DEADLINE":

        print(
            "  WARNING: No application deadline was provided."
        )

    elif status == "INVALID_DEADLINE":

        print(
            "  WARNING: Application deadline format is invalid."
        )


def deadline_allows_processing(
    deadline_info
):
    """
    Determine whether a job can continue.

    Expired jobs are stopped.

    Jobs with no deadline, urgent deadlines,
    active deadlines, and invalid deadlines
    are allowed to continue.
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
    # STEP A - DEADLINE CHECK
    # ========================================================

    deadline_info = get_deadline_information(
        job
    )

    print_deadline_information(
        job,
        deadline_info
    )

    if not deadline_allows_processing(
        deadline_info
    ):

        print()

        print(
            "  SKIPPED: application deadline has expired."
        )

        return "deadline_expired"

    # ========================================================
    # STEP B - DUPLICATE CHECK
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
    # STEP C - MATCH SCORE
    # ========================================================

    match_score = job.get(
        "match_score"
    )

    if match_score is None:

        match_score = 0

    # ========================================================
    # STEP D - DECISION
    # ========================================================

    decision = job.get(
        "decision"
    )

    if not decision:

        decision = "REVIEW"

    # ========================================================
    # STEP E - CREATE APPLICATION RECORD
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
    # STEP F - ADD TO TRACKER
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

    if not jobs:

        print(
            "No jobs available for deadline monitoring."
        )

        print()

        print(
            "Deadline monitoring is informational only."
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
        "AGENTIC JOB APPLICATION PIPELINE - VERSION 7"
    )

    print(
        "=" * 70
    )

    # ========================================================
    # STEP 1 - DATABASE
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
    # STEP 2 - LOAD JOBS
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
    # STEP 3 - VALIDATE JOBS
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
    # STEP 4 - EARLY DEADLINE SCREENING
    # ========================================================

    print()

    print(
        "STEP 4: Checking application deadlines..."
    )

    deadline_results = {
        "no_deadline": 0,
        "active": 0,
        "urgent": 0,
        "expired": 0,
        "invalid": 0
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

        elif status == "ACTIVE":

            deadline_results[
                "active"
            ] += 1

        elif status == "URGENT":

            deadline_results[
                "urgent"
            ] += 1

        elif status == "INVALID_DEADLINE":

            deadline_results[
                "invalid"
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
        f"  Urgent deadline: "
        f"{deadline_results['urgent']}"
    )

    print(
        f"  Expired: "
        f"{deadline_results['expired']}"
    )

    print(
        f"  Invalid deadline: "
        f"{deadline_results['invalid']}"
    )

    print(
        f"  Jobs continuing: "
        f"{len(deadline_valid_jobs)}"
    )

    if not deadline_valid_jobs:

        print()

        print(
            "No jobs remain after deadline screening."
        )

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
            f"{deadline_results['expired']}"
        )

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
            "Deadline monitoring is informational only."
        )

        return

    # ========================================================
    # STEP 5 - DUPLICATE DETECTION
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
    # STEP 6 - APPLICATION TRACKING
    # ========================================================

    print()

    print(
        "STEP 6: Application tracking..."
    )

    results = {
        "tracked": 0,
        "already_tracked": 0,
        "duplicates": 0,
        "deadline_expired":
            deadline_results[
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
    # STEP 7 - INFORMATIONAL DEADLINE MONITORING
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
