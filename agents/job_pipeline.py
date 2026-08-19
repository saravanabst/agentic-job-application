import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(BASE_DIR / "agents")
)

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
    get_deadline_status
)

from job_decision_engine import (
    analyze_job
)


# ============================================================
# CONFIGURATION
# ============================================================

PIPELINE_VERSION = "VERSION 10"


# ============================================================
# DEADLINE HELPERS
# ============================================================

def parse_deadline(application_deadline):
    """
    Convert a supported deadline string into a datetime object.

    Supported formats:
        YYYY-MM-DD HH:MM:SS
        YYYY-MM-DD HH:MM
        YYYY-MM-DD

    Returns:
        datetime object or None
    """

    if not application_deadline:
        return None

    deadline_text = str(
        application_deadline
    ).strip()

    deadline_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d"
    ]

    for deadline_format in deadline_formats:

        try:

            return datetime.strptime(
                deadline_text,
                deadline_format
            )

        except ValueError:

            continue

    return None


def calculate_deadline_status(
    application_deadline
):
    """
    Determine deadline status from the actual deadline date.

    The parsed deadline is authoritative.

    Returns:
        status
        days_remaining
    """

    if not application_deadline:

        return (
            "NO_DEADLINE",
            None
        )

    deadline_datetime = parse_deadline(
        application_deadline
    )

    if deadline_datetime is None:

        return (
            "INVALID_DEADLINE",
            None
        )

    difference = (
        deadline_datetime
        - datetime.now()
    )

    days_remaining = difference.days

    # --------------------------------------------------------
    # Expired
    # --------------------------------------------------------

    if difference.total_seconds() < 0:

        return (
            "EXPIRED",
            days_remaining
        )

    # --------------------------------------------------------
    # Urgent: within 24 hours
    # --------------------------------------------------------

    if difference.total_seconds() <= 86400:

        return (
            "URGENT",
            days_remaining
        )

    # --------------------------------------------------------
    # Active
    # --------------------------------------------------------

    return (
        "ACTIVE",
        days_remaining
    )


def get_deadline_information(job):
    """
    Return complete deadline information.

    The actual deadline date is used to determine whether
    the deadline is ACTIVE, URGENT, EXPIRED, or INVALID.
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
    # Calculate status from actual date
    # --------------------------------------------------------

    status, days_remaining = calculate_deadline_status(
        application_deadline
    )

    # --------------------------------------------------------
    # Optional tracker status
    #
    # Tracker status is informational only.
    # It must NOT override the actual date calculation.
    # --------------------------------------------------------

    job_id = job.get(
        "job_id"
    )

    try:

        tracker_status = get_deadline_status(
            job_id
        )

    except Exception:

        tracker_status = None

    return {
        "deadline": application_deadline,
        "status": status,
        "days_remaining": days_remaining,
        "tracker_status": tracker_status
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

    deadline = deadline_info.get(
        "deadline"
    )

    status = deadline_info.get(
        "status"
    )

    days_remaining = deadline_info.get(
        "days_remaining"
    )

    print()

    print(
        f"Deadline check: {job_id}"
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
    # Human-readable action
    # --------------------------------------------------------

    if status == "EXPIRED":

        print(
            "  ACTION: SKIP EXPIRED JOB"
        )

    elif status == "URGENT":

        print(
            "  ACTION: URGENT - DEADLINE WITHIN 24 HOURS"
        )

    elif status == "ACTIVE":

        if (
            days_remaining is not None
            and days_remaining <= 3
        ):

            print(
                "  ACTION: HIGH PRIORITY - DEADLINE WITHIN 3 DAYS"
            )

        else:

            print(
                "  ACTION: CONTINUE PROCESSING"
            )

    elif status == "NO_DEADLINE":

        print(
            "  ACTION: CONTINUE - NO DEADLINE PROVIDED"
        )

    elif status == "INVALID_DEADLINE":

        print(
            "  ACTION: REVIEW INVALID DEADLINE"
        )


def deadline_allows_processing(
    deadline_info
):
    """
    Determine whether a job can continue.

    Only EXPIRED and INVALID_DEADLINE jobs are stopped.

    Jobs without a deadline are allowed to continue.
    """

    status = deadline_info.get(
        "status"
    )

    if status in (
        "EXPIRED",
        "INVALID_DEADLINE"
    ):

        return False

    return True


# ============================================================
# JOB DECISION ENGINE
# ============================================================

def process_job_decision(job):
    """
    Run the Job Decision Engine for one job.
    """

    job_id = job.get(
        "job_id"
    )

    title = job.get(
        "title",
        ""
    )

    location = job.get(
        "location",
        ""
    )

    work_mode = job.get(
        "work_mode",
        ""
    )

    description = job.get(
        "description",
        ""
    )

    print()

    print(
        f"Decision analysis: {job_id}"
    )

    try:

        decision_result = analyze_job(
            title,
            location,
            work_mode,
            description
        )

    except Exception as error:

        print(
            f"  ERROR: Decision engine failed: {error}"
        )

        return None

    print(
        f"  Match score: "
        f"{decision_result['score']}/100"
    )

    print(
        f"  Decision: "
        f"{decision_result['decision']}"
    )

    print()

    print(
        "  SCORE BREAKDOWN"
    )

    for factor, score in decision_result[
        "score_breakdown"
    ].items():

        print(
            f"    {factor}: {score}"
        )

    print()

    print(
        "  REQUIRED SKILLS"
    )

    required_matches = decision_result.get(
        "required_matches",
        []
    )

    required_gaps = decision_result.get(
        "required_gaps",
        []
    )

    print(
        "    Matched: "
        + (
            ", ".join(required_matches)
            if required_matches
            else "None"
        )
    )

    print(
        "    Gaps: "
        + (
            ", ".join(required_gaps)
            if required_gaps
            else "None"
        )
    )

    print()

    print(
        "  PREFERRED SKILLS"
    )

    preferred_matches = decision_result.get(
        "preferred_matches",
        []
    )

    preferred_gaps = decision_result.get(
        "preferred_gaps",
        []
    )

    print(
        "    Matched: "
        + (
            ", ".join(preferred_matches)
            if preferred_matches
            else "None"
        )
    )

    print(
        "    Gaps: "
        + (
            ", ".join(preferred_gaps)
            if preferred_gaps
            else "None"
        )
    )

    print()

    print(
        "  PORTFOLIO EVIDENCE"
    )

    portfolio_evidence = decision_result.get(
        "portfolio_evidence",
        {}
    )

    if portfolio_evidence:

        for skill, projects in portfolio_evidence.items():

            print(
                f"    {skill}:"
            )

            for project in projects:

                print(
                    f"      -> {project}"
                )

    else:

        print(
            "    None"
        )

    print()

    print(
        "  RISKS"
    )

    risks = decision_result.get(
        "risks",
        []
    )

    if risks:

        for risk in risks:

            print(
                f"    WARNING: {risk}"
            )

    else:

        print(
            "    None detected."
        )

    return decision_result


# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(
    job,
    decision_result
):
    """
    Create an application tracking record.

    No application is submitted automatically.
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

    deadline_info = get_deadline_information(
        job
    )

    match_score = decision_result.get(
        "score",
        0
    )

    decision = decision_result.get(
        "decision",
        "REVIEW"
    )

    print()

    print(
        f"Processing: "
        f"{job_id} - "
        f"{company} - "
        f"{title}"
    )

    print(
        f"  Application deadline: "
        f"{deadline_info.get('deadline')}"
    )

    print(
        f"  Match score: "
        f"{match_score}/100"
    )

    print(
        f"  Decision: "
        f"{decision}"
    )

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

    created = add_application(
        application_record
    )

    if not created:

        return "already_tracked"

    print()

    print(
        "  APPLICATION RECORD CREATED"
    )

    return "tracked"


# ============================================================
# DEADLINE MONITORING
# ============================================================

def process_deadline_monitoring(
    jobs
):
    """
    Informational deadline monitoring only.

    This function does NOT submit applications.
    """

    print()

    print(
        "STEP 8: Deadline monitoring..."
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

        print(
            f"  Deadline: "
            f"{deadline_info.get('deadline')}"
        )

        print(
            f"  Deadline status: "
            f"{deadline_info.get('status')}"
        )

        days_remaining = deadline_info.get(
            "days_remaining"
        )

        if days_remaining is not None:

            print(
                f"  Days remaining: "
                f"{days_remaining}"
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
        f"AGENTIC JOB APPLICATION PIPELINE - "
        f"{PIPELINE_VERSION}"
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
                "Missing fields: "
                + ", ".join(missing_fields)
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
    # STEP 4 - DEADLINE SCREENING
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

        if status == "INVALID_DEADLINE":

            deadline_results[
                "invalid"
            ] += 1

            print(
                "  Job requires deadline review."
            )

            continue

        if status == "NO_DEADLINE":

            deadline_results[
                "no_deadline"
            ] += 1

        elif status == "URGENT":

            deadline_results[
                "urgent"
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
            f"Jobs loaded:        {len(jobs)}"
        )

        print(
            f"Valid jobs:         {len(valid_jobs)}"
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
            "Human review required: True"
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
    # STEP 6 - JOB DECISION ENGINE
    # ========================================================

    print()

    print(
        "STEP 6: Running Job Decision Engine..."
    )

    decision_results = {}

    decision_errors = 0

    for job in deadline_valid_jobs:

        job_id = job.get(
            "job_id"
        )

        if job_id in duplicate_ids:

            continue

        result = process_job_decision(
            job
        )

        if result is None:

            decision_errors += 1

            continue

        decision_results[
            job_id
        ] = result

    print()

    print(
        "JOB DECISION SUMMARY"
    )

    print(
        "-" * 70
    )

    for job in deadline_valid_jobs:

        job_id = job.get(
            "job_id"
        )

        if job_id not in decision_results:

            continue

        result = decision_results[
            job_id
        ]

        print(
            f"{job_id} | "
            f"{job.get('company', '')} | "
            f"{job.get('title', '')}"
        )

        print(
            f"  Score: "
            f"{result['score']}/100"
        )

        print(
            f"  Decision: "
            f"{result['decision']}"
        )

    # ========================================================
    # STEP 7 - APPLICATION TRACKING
    # ========================================================

    print()

    print(
        "STEP 7: Application tracking..."
    )

    results = {
        "tracked": 0,
        "already_tracked": 0,
        "duplicates": 0,
        "deadline_expired":
            deadline_results["expired"],
        "decision_errors":
            decision_errors
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

        decision_result = decision_results.get(
            job_id
        )

        if decision_result is None:

            continue

        result = process_job(
            job,
            decision_result
        )

        if result in results:

            results[
                result
            ] += 1

    # ========================================================
    # STEP 8 - DEADLINE MONITORING
    # ========================================================

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
        f"Decision errors:     "
        f"{results['decision_errors']}"
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

    print(
        "Human review required: True"
    )

    print()

    print(
        "Deadline monitoring is informational only."
    )

    print()

    print(
        f"Completed at:       "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":

    main()