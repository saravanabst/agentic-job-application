import json
from pathlib import Path
from datetime import datetime

from job_loader import load_all_jobs, validate_job
from duplicate_detector import find_duplicates
from application_tracker import (
    initialize_database,
    application_exists,
    add_application
)


BASE_DIR = Path(__file__).resolve().parent.parent


def process_job(job):
    """Process one valid job through the tracking layer."""

    job_id = job.get("job_id")

    company = job.get("company", "")
    title = job.get("title", "")

    print()
    print(f"Processing: {job_id} - {company} - {title}")

    # Check whether this job is already in our
    # application tracking database.
    existing = application_exists(job_id)

    if existing:

        print("  SKIPPED: already tracked")
        print(f"  Existing status: {existing[1]}")

        return "already_tracked"

    # The decision engine will eventually provide
    # these values automatically.
    #
    # For now, use values already stored in the
    # job record if they exist.
    match_score = job.get("match_score")
    decision = job.get("decision")

    if match_score is None:
        match_score = 0

    if not decision:
        decision = "REVIEW"

    application_record = {
        "job_id": job_id,
        "company": company,
        "title": title,
        "location": job.get("location", ""),
        "work_mode": job.get("work_mode", ""),
        "source": job.get("source", ""),
        "source_job_id": job.get(
            "source_job_id",
            ""
        ),
        "url": job.get("url", ""),
        "match_score": match_score,
        "decision": decision,
        "discovered_at": job.get(
            "discovered_at",
            ""
        ),
        "notes": job.get("notes", "")
    }

    add_application(application_record)

    return "tracked"


def main():

    print()
    print("AGENTIC JOB APPLICATION PIPELINE")
    print("=" * 70)

    # --------------------------------------------------
    # STEP 1 — DATABASE
    # --------------------------------------------------

    print()
    print("STEP 1: Initializing application database...")

    initialize_database()

    print("Database ready.")

    # --------------------------------------------------
    # STEP 2 — LOAD JOBS
    # --------------------------------------------------

    print()
    print("STEP 2: Loading jobs...")

    jobs = load_all_jobs()

    print(f"Jobs loaded: {len(jobs)}")

    if not jobs:

        print("No jobs found.")

        return

    # --------------------------------------------------
    # STEP 3 — VALIDATE JOBS
    # --------------------------------------------------

    print()
    print("STEP 3: Validating jobs...")

    valid_jobs = []

    for job in jobs:

        missing_fields = validate_job(job)

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

        valid_jobs.append(job)

    print(
        f"Valid jobs: "
        f"{len(valid_jobs)}/{len(jobs)}"
    )

    # --------------------------------------------------
    # STEP 4 — DUPLICATE DETECTION
    # --------------------------------------------------

    print()
    print("STEP 4: Checking duplicates...")

    duplicates = find_duplicates(valid_jobs)

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

    # --------------------------------------------------
    # STEP 5 — APPLICATION TRACKING
    # --------------------------------------------------

    print()
    print("STEP 5: Application tracking...")

    results = {
        "tracked": 0,
        "already_tracked": 0,
        "duplicates": 0
    }

    for job in valid_jobs:

        job_id = job.get("job_id")

        if job_id in duplicate_ids:

            print()
            print(
                f"SKIPPED DUPLICATE: "
                f"{job_id}"
            )

            results["duplicates"] += 1

            continue

        result = process_job(job)

        if result in results:

            results[result] += 1

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    print(
        f"Jobs loaded:       {len(jobs)}"
    )

    print(
        f"Valid jobs:        {len(valid_jobs)}"
    )

    print(
        f"Duplicates:        {results['duplicates']}"
    )

    print(
        f"Newly tracked:     {results['tracked']}"
    )

    print(
        f"Already tracked:   {results['already_tracked']}"
    )

    print(
        f"Completed at:      "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )


if __name__ == "__main__":
    main()