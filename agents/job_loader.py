import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_RAW_DIR = BASE_DIR / "jobs" / "raw"


def load_job(file_path):
    """Load one job JSON file."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_all_jobs():
    """Load all JSON job records from jobs/raw."""

    jobs = []

    for file_path in sorted(
        JOBS_RAW_DIR.glob("*.json")
    ):
        try:
            job = load_job(file_path)

            jobs.append(job)

        except json.JSONDecodeError as error:

            print(
                f"ERROR: Invalid JSON: "
                f"{file_path}"
            )

            print(error)

    return jobs


def validate_job(job):
    """Check that the minimum job fields exist."""

    required_fields = [
        "job_id",
        "company",
        "title",
        "location",
        "work_mode",
        "employment_type",
        "description",
        "application_status"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in job
    ]

    return missing_fields


def print_job_summary(job):
    """Display a readable job summary."""

    print()
    print("=" * 60)
    print("JOB RECORD")
    print("=" * 60)

    print(f"Job ID:          {job.get('job_id')}")
    print(f"Company:         {job.get('company')}")
    print(f"Title:           {job.get('title')}")
    print(f"Location:        {job.get('location')}")
    print(f"Work Mode:       {job.get('work_mode')}")
    print(
        f"Employment Type: "
        f"{job.get('employment_type')}"
    )
    print(
        f"Application:     "
        f"{job.get('application_status')}"
    )

    print()
    print("Description:")
    print(job.get("description", ""))


def main():

    print()
    print("JOB DATA LOADER")
    print("=" * 60)

    jobs = load_all_jobs()

    print(
        f"Jobs found: {len(jobs)}"
    )

    if not jobs:
        print(
            "No job records found."
        )
        return

    valid_jobs = 0

    for job in jobs:

        missing_fields = validate_job(job)

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
                print(f"  - {field}")

            continue

        valid_jobs += 1

        print_job_summary(job)

    print()
    print("=" * 60)
    print(
        f"Valid jobs: "
        f"{valid_jobs}/{len(jobs)}"
    )


if __name__ == "__main__":
    main()
