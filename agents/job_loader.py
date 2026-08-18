import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_RAW_DIR = BASE_DIR / "jobs" / "raw"


def load_job(file_path):
    """Load one job JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def load_all_jobs():
    """Load all JSON job records from jobs/raw."""

    jobs = []

    for file_path in sorted(
        JOBS_RAW_DIR.glob("*.json")
    ):

        try:

            job = load_job(
                file_path
            )

            jobs.append(
                job
            )

        except json.JSONDecodeError as error:

            print()
            print(
                f"ERROR: Invalid JSON: "
                f"{file_path}"
            )

            print(error)

    return jobs


def validate_job(job):
    """
    Check that the minimum job fields exist.

    application_deadline is part of the standard
    job schema. It may be an empty string when
    no deadline has been provided.
    """

    required_fields = [
        "job_id",
        "company",
        "title",
        "location",
        "work_mode",
        "employment_type",
        "description",
        "application_deadline",
        "application_status"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in job
    ]

    return missing_fields


def get_application_deadline(job):
    """
    Return the application deadline.

    An empty or missing deadline is represented
    as None. No deadline is invented.
    """

    deadline = job.get(
        "application_deadline"
    )

    if deadline is None:
        return None

    if isinstance(
        deadline,
        str
    ):

        deadline = deadline.strip()

        if not deadline:
            return None

    return deadline


def print_job_summary(job):
    """Display a readable job summary."""

    print()
    print("=" * 70)
    print("JOB RECORD")
    print("=" * 70)

    print(
        f"Job ID:              "
        f"{job.get('job_id')}"
    )

    print(
        f"Company:             "
        f"{job.get('company')}"
    )

    print(
        f"Title:               "
        f"{job.get('title')}"
    )

    print(
        f"Location:            "
        f"{job.get('location')}"
    )

    print(
        f"Work Mode:           "
        f"{job.get('work_mode')}"
    )

    print(
        f"Employment Type:     "
        f"{job.get('employment_type')}"
    )

    deadline = get_application_deadline(
        job
    )

    if deadline:

        print(
            f"Application Deadline:"
            f" {deadline}"
        )

    else:

        print(
            "Application Deadline:"
            " NOT PROVIDED"
        )

    print(
        f"Application Status:   "
        f"{job.get('application_status')}"
    )

    print()
    print("Description:")
    print(
        job.get(
            "description",
            ""
        )
    )


def main():

    print()
    print(
        "JOB DATA LOADER - VERSION 2"
    )

    print(
        "=" * 70
    )

    jobs = load_all_jobs()

    print(
        f"Jobs found: "
        f"{len(jobs)}"
    )

    if not jobs:

        print(
            "No job records found."
        )

        return

    valid_jobs = 0

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
                "Missing fields:"
            )

            for field in missing_fields:

                print(
                    f"  - {field}"
                )

            continue

        valid_jobs += 1

        print_job_summary(
            job
        )

    print()
    print("=" * 70)

    print(
        f"Valid jobs: "
        f"{valid_jobs}/{len(jobs)}"
    )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()