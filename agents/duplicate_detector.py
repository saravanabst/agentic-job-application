import hashlib
import re


def normalize_text(value):
    """Normalize text for comparison."""

    if not value:
        return ""

    value = value.lower().strip()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def create_identity_keys(job):
    """
    Create multiple identities for a job.

    These identities allow us to detect the
    same job across different job sources.
    """

    source_job_id = normalize_text(
        job.get("source_job_id", "")
    )

    url = normalize_text(
        job.get("url", "")
    )

    company = normalize_text(
        job.get("company", "")
    )

    title = normalize_text(
        job.get("title", "")
    )

    location = normalize_text(
        job.get("location", "")
    )

    keys = []

    # Strong signal: exact URL
    if url:
        keys.append(
            (
                "url",
                hashlib.sha256(
                    url.encode("utf-8")
                ).hexdigest()
            )
        )

    # Strong signal: same job ID + same company + same title
    if source_job_id:
        identity = (
            f"{source_job_id}|"
            f"{company}|"
            f"{title}"
        )

        keys.append(
            (
                "source_job_id",
                hashlib.sha256(
                    identity.encode("utf-8")
                ).hexdigest()
            )
        )

    # Medium/strong signal:
    # same company + title + location
    if company and title and location:

        identity = (
            f"{company}|"
            f"{title}|"
            f"{location}"
        )

        keys.append(
            (
                "company_title_location",
                hashlib.sha256(
                    identity.encode("utf-8")
                ).hexdigest()
            )
        )

    return keys


def find_duplicates(jobs):
    """
    Find duplicate jobs using multiple identity keys.
    """

    known_keys = {}
    duplicates = []

    for job in jobs:

        job_id = job.get(
            "job_id",
            "UNKNOWN"
        )

        identity_keys = create_identity_keys(
            job
        )

        duplicate_found = False

        for key_type, fingerprint in identity_keys:

            if fingerprint in known_keys:

                original_job_id = known_keys[
                    fingerprint
                ]

                duplicates.append({
                    "job_id": job_id,
                    "duplicate_of": original_job_id,
                    "match_type": key_type,
                    "fingerprint": fingerprint
                })

                duplicate_found = True

                break

        # Register this job's identities
        if not duplicate_found:

            for key_type, fingerprint in identity_keys:

                if fingerprint not in known_keys:

                    known_keys[
                        fingerprint
                    ] = job_id

    return duplicates


def main():

    print()
    print("DUPLICATE JOB DETECTOR")
    print("=" * 60)

    # Test jobs from different sources
    jobs = [
        {
            "job_id": "job_001",
            "source": "seek",
            "source_job_id": "12345",
            "company": "Example Analytics Company",
            "title": "Data Analyst",
            "location": "Auckland, New Zealand",
            "url": "https://example.com/job/12345"
        },
        {
            "job_id": "job_002",
            "source": "linkedin",
            "source_job_id": "12345",
            "company": "Example Analytics Company",
            "title": "Data Analyst",
            "location": "Auckland, New Zealand",
            "url": "https://linkedin.com/jobs/12345"
        },
        {
            "job_id": "job_003",
            "source": "seek",
            "source_job_id": "99999",
            "company": "Another Company",
            "title": "BI Analyst",
            "location": "Hamilton, New Zealand",
            "url": "https://example.com/job/99999"
        }
    ]

    for job in jobs:

        print()
        print(
            f"{job['job_id']}:"
        )

        keys = create_identity_keys(
            job
        )

        for key_type, fingerprint in keys:

            print(
                f"  {key_type}: "
                f"{fingerprint[:16]}..."
            )

    duplicates = find_duplicates(
        jobs
    )

    print()
    print("-" * 60)

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


if __name__ == "__main__":
    main()