import json
import shutil
import sys
from pathlib import Path


# ============================================================
# APPLICATION PACKAGE AGENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

# ============================================================
# IMPORT APPLICATION TRACKER
# ============================================================

sys.path.insert(0, str(BASE_DIR / "agents"))

from application_tracker import (
    initialize_database,
    get_application,
    update_status,
)

TAILORING_PLAN = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
    / f"{JOB_ID}_tailoring_plan.json"
)

RESUME_PDF = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "tailored"
    / "resume.pdf"
)

COVER_LETTER_PDF = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "cover_letter"
    / "cover_letter.pdf"
)

PACKAGE_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "application_package"
)


# ============================================================
# JSON LOADER
# ============================================================

def load_json(file_path):
    """Load JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# FILE CHECK
# ============================================================

def check_file(file_path):
    """
    Check whether a required application file exists
    and is not empty.
    """

    if not file_path.exists():
        return {
            "exists": False,
            "valid": False,
            "size_bytes": 0
        }

    size = file_path.stat().st_size

    return {
        "exists": True,
        "valid": size > 0,
        "size_bytes": size
    }


# ============================================================
# APPLICATION VALIDATION
# ============================================================

def validate_application(
    tailoring,
    resume_status,
    cover_letter_status
):
    """
    Validate the application package before human review.
    """

    job = tailoring.get(
        "job",
        {}
    )

    safety = tailoring.get(
        "safety",
        {}
    )

    errors = []
    warnings = []

    # --------------------------------------------------------
    # Resume validation
    # --------------------------------------------------------

    if not resume_status["exists"]:
        errors.append(
            "ATS resume PDF is missing."
        )

    elif not resume_status["valid"]:
        errors.append(
            "ATS resume PDF exists but is empty."
        )

    # --------------------------------------------------------
    # Cover letter validation
    # --------------------------------------------------------

    if not cover_letter_status["exists"]:
        errors.append(
            "Cover letter PDF is missing."
        )

    elif not cover_letter_status["valid"]:
        errors.append(
            "Cover letter PDF exists but is empty."
        )

    # --------------------------------------------------------
    # Job information validation
    # --------------------------------------------------------

    if not job.get("job_id"):
        warnings.append(
            "Job ID is missing."
        )

    if not job.get("title"):
        warnings.append(
            "Job title is missing."
        )

    if not job.get("company"):
        warnings.append(
            "Company name is missing."
        )

    if not job.get("location"):
        warnings.append(
            "Job location is missing."
        )

    # --------------------------------------------------------
    # Skill validation
    # --------------------------------------------------------

    required_skills = tailoring.get(
        "matched_required_skills",
        []
    )

    required_gaps = tailoring.get(
        "required_skill_gaps",
        []
    )

    preferred_gaps = tailoring.get(
        "preferred_skill_gaps",
        []
    )

    if not required_skills:
        warnings.append(
            "No matched required skills were detected."
        )

    if required_gaps:
        warnings.append(
            "Required skill gaps remain: "
            + ", ".join(required_gaps)
        )

    if preferred_gaps:
        warnings.append(
            "Preferred skill gaps remain: "
            + ", ".join(preferred_gaps)
        )

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    safety_checks = [
        "invented_experience",
        "invented_skills",
        "invented_education",
        "invented_employment",
        "automatic_submission"
    ]

    for check in safety_checks:

        if safety.get(check, False):

            errors.append(
                "Safety violation detected: "
                + check
            )

    if safety.get(
        "human_review_required",
        True
    ):
        warnings.append(
            "Human review is required before submission."
        )

    # --------------------------------------------------------
    # Overall status
    # --------------------------------------------------------

    if errors:
        status = "NOT_READY"

    else:
        status = "READY_FOR_HUMAN_REVIEW"

    return {
        "status": status,
        "errors": errors,
        "warnings": warnings
    }


# ============================================================
# COPY APPLICATION FILES
# ============================================================

def copy_application_files():

    PACKAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    resume_destination = (
        PACKAGE_DIR
        / "resume.pdf"
    )

    cover_letter_destination = (
        PACKAGE_DIR
        / "cover_letter.pdf"
    )

    shutil.copy2(
        RESUME_PDF,
        resume_destination
    )

    shutil.copy2(
        COVER_LETTER_PDF,
        cover_letter_destination
    )

    return (
        resume_destination,
        cover_letter_destination
    )


# ============================================================
# CREATE APPLICATION PACKAGE JSON
# ============================================================

def create_package_record(
    tailoring,
    validation,
    resume_status,
    cover_letter_status,
    resume_destination,
    cover_letter_destination
):

    job = tailoring.get(
        "job",
        {}
    )

    package = {

        "application_package_version": "1.0",

        "application_status": (
            validation["status"]
        ),

        "job": {
            "job_id": job.get(
                "job_id",
                ""
            ),

            "title": job.get(
                "title",
                ""
            ),

            "company": job.get(
                "company",
                ""
            ),

            "location": job.get(
                "location",
                ""
            ),

            "work_mode": job.get(
                "work_mode",
                ""
            )
        },

        "files": {

            "resume": {
                "source": str(
                    RESUME_PDF
                ),
                "package_file": str(
                    resume_destination
                ),
                "exists": resume_status[
                    "exists"
                ],
                "size_bytes": resume_status[
                    "size_bytes"
                ]
            },

            "cover_letter": {
                "source": str(
                    COVER_LETTER_PDF
                ),
                "package_file": str(
                    cover_letter_destination
                ),
                "exists": cover_letter_status[
                    "exists"
                ],
                "size_bytes": cover_letter_status[
                    "size_bytes"
                ]
            }
        },

        "skills": {

            "matched_required": (
                tailoring.get(
                    "matched_required_skills",
                    []
                )
            ),

            "required_gaps": (
                tailoring.get(
                    "required_skill_gaps",
                    []
                )
            ),

            "matched_preferred": (
                tailoring.get(
                    "matched_preferred_skills",
                    []
                )
            ),

            "preferred_gaps": (
                tailoring.get(
                    "preferred_skill_gaps",
                    []
                )
            )
        },

        "recommended_projects": (
            tailoring.get(
                "recommended_projects",
                []
            )
        ),

        "validation": validation,

        "human_review": {

            "required": True,

            "automatic_submission": False,

            "review_items": [
                "Confirm job title and company.",
                "Review ATS resume content.",
                "Review cover letter content.",
                "Confirm contact information.",
                "Confirm required skills are represented accurately.",
                "Confirm all experience and education claims are truthful.",
                "Confirm application deadline.",
                "Confirm application portal and submission instructions.",
                "Submit manually only after final approval."
            ]
        }
    }

    return package


# ============================================================
# PRINT APPLICATION PACKAGE
# ============================================================

def print_package(
    package
):

    print()
    print(
        "APPLICATION PACKAGE AGENT"
    )
    print("=" * 65)

    job = package["job"]

    print()
    print(
        f"Job:      {job['title']}"
    )

    print(
        f"Company:  {job['company']}"
    )

    print(
        f"Location: {job['location']}"
    )

    print()
    print(
        "APPLICATION STATUS"
    )

    print(
        f"  {package['application_status']}"
    )

    print()
    print(
        "APPLICATION FILES"
    )

    resume = package["files"]["resume"]

    print(
        "  Resume PDF:"
    )

    print(
        f"      {resume['package_file']}"
    )

    print(
        f"      Size: {resume['size_bytes']} bytes"
    )

    cover_letter = package[
        "files"
    ]["cover_letter"]

    print()
    print(
        "  Cover Letter PDF:"
    )

    print(
        f"      {cover_letter['package_file']}"
    )

    print(
        f"      Size: {cover_letter['size_bytes']} bytes"
    )

    print()
    print(
        "MATCHED REQUIRED SKILLS"
    )

    matched_required = package[
        "skills"
    ]["matched_required"]

    if matched_required:

        for skill in matched_required:
            print(
                f"  MATCH: {skill}"
            )

    else:
        print(
            "  None"
        )

    print()
    print(
        "REQUIRED SKILL GAPS"
    )

    required_gaps = package[
        "skills"
    ]["required_gaps"]

    if required_gaps:

        for skill in required_gaps:
            print(
                f"  GAP: {skill}"
            )

    else:
        print(
            "  None"
        )

    print()
    print(
        "WARNINGS"
    )

    warnings = package[
        "validation"
    ]["warnings"]

    if warnings:

        for warning in warnings:
            print(
                f"  WARNING: {warning}"
            )

    else:
        print(
            "  None"
        )

    print()
    print(
        "ERRORS"
    )

    errors = package[
        "validation"
    ]["errors"]

    if errors:

        for error in errors:
            print(
                f"  ERROR: {error}"
            )

    else:
        print(
            "  None"
        )

    print()
    print(
        "HUMAN REVIEW"
    )

    print(
        "  Required: True"
    )

    print(
        "  Automatic submission: False"
    )

    print()
    print(
        "REVIEW CHECKLIST"
    )

    for item in package[
        "human_review"
    ]["review_items"]:

        print(
            f"  [ ] {item}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "APPLICATION PACKAGE AGENT TEST - VERSION 1"
    )
    print("=" * 65)

    # --------------------------------------------------------
    # Check tailoring plan
    # --------------------------------------------------------

    if not TAILORING_PLAN.exists():

        print()
        print(
            "ERROR: Tailoring plan not found:"
        )

        print(
            TAILORING_PLAN
        )

        return

    # --------------------------------------------------------
    # Load tailoring plan
    # --------------------------------------------------------

    tailoring = load_json(
        TAILORING_PLAN
    )

    # --------------------------------------------------------
    # Check application files
    # --------------------------------------------------------

    resume_status = check_file(
        RESUME_PDF
    )

    cover_letter_status = check_file(
        COVER_LETTER_PDF
    )

    # --------------------------------------------------------
    # Validate application
    # --------------------------------------------------------

    validation = validate_application(
        tailoring,
        resume_status,
        cover_letter_status
    )

    # --------------------------------------------------------
    # Stop if required files are missing
    # --------------------------------------------------------

    if validation["status"] == "NOT_READY":

        print()
        print(
            "APPLICATION PACKAGE NOT READY"
        )

        print()

        for error in validation["errors"]:

            print(
                f"ERROR: {error}"
            )

        print()

        return

    # --------------------------------------------------------
    # Copy PDFs into package
    # --------------------------------------------------------

    (
        resume_destination,
        cover_letter_destination
    ) = copy_application_files()

    # --------------------------------------------------------
    # Create package record
    # --------------------------------------------------------

    package = create_package_record(
        tailoring,
        validation,
        resume_status,
        cover_letter_status,
        resume_destination,
        cover_letter_destination
    )

    # --------------------------------------------------------
    # Save package JSON
    # --------------------------------------------------------

    package_json = (
        PACKAGE_DIR
        / "application_package.json"
    )

    with open(
        package_json,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            package,
            file,
            indent=4,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print_package(
        package
    )

    print()
    print(
        "APPLICATION PACKAGE CREATED"
    )

    print(
        f"Package directory:"
    )

    print(
        PACKAGE_DIR
    )

    print()
    print(
        "Package manifest:"
    )

    print(
        package_json
    )


if __name__ == "__main__":
    main()