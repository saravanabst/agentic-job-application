import json
import sys
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

TAILORING_PLAN = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
    / f"{JOB_ID}_tailoring_plan.json"
)

PACKAGE_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "application_package"
)

OUTPUT_FILE = PACKAGE_DIR / "qa_report.json"


def load_json(file_path):
    """Load JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def check_file_exists(
    file_path,
    label,
    errors
):
    """Check whether a required file exists."""

    if not file_path.exists():

        errors.append(
            f"{label} is missing: {file_path}"
        )

        return False

    if file_path.stat().st_size == 0:

        errors.append(
            f"{label} is empty: {file_path}"
        )

        return False

    return True


def check_pdf(
    file_path,
    label,
    errors,
    warnings
):
    """Perform basic PDF validation."""

    if not check_file_exists(
        file_path,
        label,
        errors
    ):
        return False

    try:

        with open(
            file_path,
            "rb"
        ) as file:

            header = file.read(5)

        if header != b"%PDF-":

            errors.append(
                f"{label} does not appear to be a valid PDF."
            )

            return False

    except OSError as error:

        errors.append(
            f"Unable to read {label}: {error}"
        )

        return False

    size = file_path.stat().st_size

    if size < 1000:

        warnings.append(
            f"{label} is unusually small: {size} bytes."
        )

    return True


def check_manifest(
    manifest,
    errors,
    warnings
):
    """Validate application package manifest."""

    required_fields = [
        "application_package_version",
        "application_status",
        "job",
        "files",
        "skills",
        "recommended_projects",
        "validation",
        "human_review"
    ]

    for field in required_fields:

        if field not in manifest:

            errors.append(
                "Application manifest is missing field: "
                + field
            )

    if manifest.get(
        "application_status"
    ) != "READY_FOR_HUMAN_REVIEW":

        warnings.append(
            "Application status is not "
            "READY_FOR_HUMAN_REVIEW."
        )

    human_review = manifest.get(
        "human_review",
        {}
    )

    if human_review.get(
        "required"
    ) is not True:

        errors.append(
            "Human review is not explicitly required."
        )

    if human_review.get(
        "automatic_submission"
    ) is True:

        errors.append(
            "Automatic submission is enabled. "
            "This is not permitted."
        )


def check_job_details(
    tailoring,
    manifest,
    errors,
    warnings
):
    """Verify job details are consistent."""

    tailoring_job = tailoring.get(
        "job",
        {}
    )

    manifest_job = manifest.get(
        "job",
        {}
    )

    fields = [
        "job_id",
        "company",
        "title",
        "location"
    ]

    for field in fields:

        tailoring_value = str(
            tailoring_job.get(
                field,
                ""
            )
        ).strip()

        manifest_value = str(
            manifest_job.get(
                field,
                ""
            )
        ).strip()

        if (
            tailoring_value
            and manifest_value
            and tailoring_value.lower()
            != manifest_value.lower()
        ):

            errors.append(
                f"Job {field} mismatch: "
                f"tailoring plan='{tailoring_value}', "
                f"manifest='{manifest_value}'"
            )


def check_required_skills(
    tailoring,
    manifest,
    errors,
    warnings
):
    """
    Verify that required skills from the tailoring plan
    are correctly represented in the application manifest.
    """

    required_skills = tailoring.get(
        "matched_required_skills",
        []
    )

    required_gaps = tailoring.get(
        "required_skill_gaps",
        []
    )

    manifest_skills = manifest.get(
        "skills",
        {}
    )

    manifest_matches = manifest_skills.get(
        "matched_required",
        []
    )

    manifest_gaps = manifest_skills.get(
        "required_gaps",
        []
    )

    # --------------------------------------------------
    # Check tailoring plan for unresolved required gaps
    # --------------------------------------------------

    if required_gaps:

        errors.append(
            "Required skill gaps remain in tailoring plan: "
            + ", ".join(required_gaps)
        )

    # --------------------------------------------------
    # Check application manifest for unresolved gaps
    # --------------------------------------------------

    if manifest_gaps:

        errors.append(
            "Required skill gaps remain in application "
            "package manifest: "
            + ", ".join(manifest_gaps)
        )

    # --------------------------------------------------
    # Compare matched required skills
    # --------------------------------------------------

    for skill in required_skills:

        if skill not in manifest_matches:

            errors.append(
                "Required skill missing from application "
                "package manifest: "
                + skill
            )


def check_preferred_skills(
    tailoring,
    manifest,
    warnings
):
    """
    Check preferred skills.

    Preferred gaps are warnings rather than errors because
    preferred skills are not mandatory requirements.
    """

    tailoring_preferred_gaps = tailoring.get(
        "preferred_skill_gaps",
        []
    )

    manifest_skills = manifest.get(
        "skills",
        {}
    )

    manifest_preferred_gaps = manifest_skills.get(
        "preferred_gaps",
        []
    )

    combined_gaps = []

    for skill in (
        tailoring_preferred_gaps
        + manifest_preferred_gaps
    ):

        if skill not in combined_gaps:

            combined_gaps.append(
                skill
            )

    if combined_gaps:

        warnings.append(
            "Preferred skill gaps remain: "
            + ", ".join(combined_gaps)
        )


def check_projects(
    tailoring,
    manifest,
    errors,
    warnings
):
    """Verify recommended projects are consistent."""

    tailoring_projects = tailoring.get(
        "recommended_projects",
        []
    )

    manifest_projects = manifest.get(
        "recommended_projects",
        []
    )

    tailoring_names = [
        project.get(
            "project",
            ""
        )
        for project in tailoring_projects
    ]

    manifest_names = [
        project.get(
            "project",
            ""
        )
        for project in manifest_projects
    ]

    for project_name in tailoring_names:

        if project_name not in manifest_names:

            errors.append(
                "Recommended project missing from "
                "application package: "
                + project_name
            )


def check_validation_section(
    manifest,
    errors,
    warnings
):
    """Validate the manifest validation section."""

    validation = manifest.get(
        "validation",
        {}
    )

    status = validation.get(
        "status",
        ""
    )

    validation_errors = validation.get(
        "errors",
        []
    )

    validation_warnings = validation.get(
        "warnings",
        []
    )

    if validation_errors:

        errors.extend(
            [
                "Application package validation error: "
                + str(error)
                for error in validation_errors
            ]
        )

    if validation_warnings:

        for warning in validation_warnings:

            warning_text = str(
                warning
            )

            # Preferred skill gaps are already handled
            # separately by check_preferred_skills().
            if (
                "Preferred skill gaps remain"
                not in warning_text
                and
                "Human review is required"
                not in warning_text
            ):

                warnings.append(
                    "Application package validation warning: "
                    + warning_text
                )

    if status not in [
        "READY_FOR_HUMAN_REVIEW",
        ""
    ]:

        warnings.append(
            "Application package validation status: "
            + str(status)
        )


def check_safety(
    tailoring,
    manifest,
    errors,
    warnings
):
    """Validate safety controls."""

    tailoring_safety = tailoring.get(
        "safety",
        {}
    )

    manifest_human_review = manifest.get(
        "human_review",
        {}
    )

    safety_flags = [
        "invented_experience",
        "invented_skills",
        "invented_education",
        "invented_employment"
    ]

    for flag in safety_flags:

        if tailoring_safety.get(
            flag,
            False
        ) is True:

            errors.append(
                "Safety violation detected: "
                + flag
            )

    if manifest_human_review.get(
        "automatic_submission",
        False
    ) is True:

        errors.append(
            "Automatic submission must remain disabled."
        )

    if manifest_human_review.get(
        "required",
        False
    ) is not True:

        errors.append(
            "Human review must remain required."
        )


def create_qa_report(
    tailoring,
    manifest
):
    """Run all application QA checks."""

    errors = []
    warnings = []

    resume_file = (
        PACKAGE_DIR
        / "resume.pdf"
    )

    cover_letter_file = (
        PACKAGE_DIR
        / "cover_letter.pdf"
    )

    manifest_file = (
        PACKAGE_DIR
        / "application_package.json"
    )

    checks = {}

    # --------------------------------------------------
    # Package directory
    # --------------------------------------------------

    checks[
        "package_directory"
    ] = PACKAGE_DIR.exists()

    if not PACKAGE_DIR.exists():

        errors.append(
            "Application package directory is missing: "
            + str(PACKAGE_DIR)
        )

        return {
            "qa_version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "status": "QA_FAILED",
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "human_review_required": True,
            "automatic_submission": False,
            "approval": {
                "approved": False,
                "approved_by_human": False
            }
        }

    # --------------------------------------------------
    # Resume PDF
    # --------------------------------------------------

    checks[
        "resume_pdf"
    ] = check_pdf(
        resume_file,
        "Resume PDF",
        errors,
        warnings
    )

    # --------------------------------------------------
    # Cover letter PDF
    # --------------------------------------------------

    checks[
        "cover_letter_pdf"
    ] = check_pdf(
        cover_letter_file,
        "Cover Letter PDF",
        errors,
        warnings
    )

    # --------------------------------------------------
    # Manifest
    # --------------------------------------------------

    checks[
        "application_manifest"
    ] = check_file_exists(
        manifest_file,
        "Application manifest",
        errors
    )

    # --------------------------------------------------
    # Manifest structure
    # --------------------------------------------------

    check_manifest(
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Job consistency
    # --------------------------------------------------

    check_job_details(
        tailoring,
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Required skills
    # --------------------------------------------------

    check_required_skills(
        tailoring,
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Preferred skills
    # --------------------------------------------------

    check_preferred_skills(
        tailoring,
        manifest,
        warnings
    )

    # --------------------------------------------------
    # Projects
    # --------------------------------------------------

    check_projects(
        tailoring,
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Validation section
    # --------------------------------------------------

    check_validation_section(
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Safety
    # --------------------------------------------------

    check_safety(
        tailoring,
        manifest,
        errors,
        warnings
    )

    # --------------------------------------------------
    # Final QA status
    # --------------------------------------------------

    if errors:

        status = "QA_FAILED"

    elif warnings:

        status = "QA_PASSED_WITH_WARNINGS"

    else:

        status = "QA_PASSED"

    return {
        "qa_version": "2.0",

        "timestamp": datetime.now().isoformat(),

        "status": status,

        "job": {
            "job_id": tailoring.get(
                "job",
                {}
            ).get(
                "job_id",
                ""
            ),

            "company": tailoring.get(
                "job",
                {}
            ).get(
                "company",
                ""
            ),

            "title": tailoring.get(
                "job",
                {}
            ).get(
                "title",
                ""
            ),

            "location": tailoring.get(
                "job",
                {}
            ).get(
                "location",
                ""
            )
        },

        "checks": checks,

        "errors": errors,

        "warnings": warnings,

        "human_review_required": True,

        "automatic_submission": False,

        "approval": {
            "approved": False,
            "approved_by_human": False
        }
    }


def save_report(report):
    """Save QA report."""

    PACKAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )


def print_report(report):
    """Display QA results."""

    print()
    print(
        "APPLICATION QA AGENT"
    )
    print("=" * 65)

    job = report.get(
        "job",
        {}
    )

    print()
    print(
        f"Job:      "
        f"{job.get('title', '')}"
    )

    print(
        f"Company:  "
        f"{job.get('company', '')}"
    )

    print(
        f"Location: "
        f"{job.get('location', '')}"
    )

    print()
    print(
        "QA STATUS"
    )

    print(
        f"  {report['status']}"
    )

    print()
    print(
        "CHECKS"
    )

    for check, result in report[
        "checks"
    ].items():

        display_name = check.replace(
            "_",
            " "
        ).title()

        print(
            f"  {display_name}: "
            f"{'PASS' if result else 'FAIL'}"
        )

    print()
    print(
        "ERRORS"
    )

    if report["errors"]:

        for error in report["errors"]:

            print(
                f"  ERROR: {error}"
            )

    else:

        print(
            "  None"
        )

    print()
    print(
        "WARNINGS"
    )

    if report["warnings"]:

        for warning in report["warnings"]:

            print(
                f"  WARNING: {warning}"
            )

    else:

        print(
            "  None"
        )

    print()
    print(
        "SAFETY"
    )

    print(
        f"  Human review required: "
        f"{report['human_review_required']}"
    )

    print(
        f"  Automatic submission: "
        f"{report['automatic_submission']}"
    )

    print()
    print(
        "APPROVAL"
    )

    print(
        f"  Approved: "
        f"{report['approval']['approved']}"
    )

    print(
        f"  Approved by human: "
        f"{report['approval']['approved_by_human']}"
    )

    print()
    print(
        "QA REPORT SAVED:"
    )

    print(
        OUTPUT_FILE
    )


def main():

    print()
    print(
        "APPLICATION QA AGENT TEST - VERSION 2"
    )
    print("=" * 65)

    if not TAILORING_PLAN.exists():

        print()
        print(
            "ERROR: Tailoring plan not found:"
        )

        print(
            TAILORING_PLAN
        )

        return

    if not PACKAGE_DIR.exists():

        print()
        print(
            "ERROR: Application package directory "
            "not found:"
        )

        print(
            PACKAGE_DIR
        )

        return

    manifest_file = (
        PACKAGE_DIR
        / "application_package.json"
    )

    if not manifest_file.exists():

        print()
        print(
            "ERROR: Application package manifest "
            "not found:"
        )

        print(
            manifest_file
        )

        return

    tailoring = load_json(
        TAILORING_PLAN
    )

    manifest = load_json(
        manifest_file
    )

    report = create_qa_report(
        tailoring,
        manifest
    )

    save_report(
        report
    )

    print_report(
        report
    )


if __name__ == "__main__":
    main()