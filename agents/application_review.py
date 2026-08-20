import json
import sys
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

PACKAGE_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "application_package"
)

APPLICATION_MANIFEST = (
    PACKAGE_DIR
    / "application_package.json"
)

QA_REPORT = (
    PACKAGE_DIR
    / "qa_report.json"
)

REVIEW_DECISION = (
    PACKAGE_DIR
    / "review_decision.json"
)


def load_json(file_path):
    """Load a JSON file safely."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def save_json(file_path, data):
    """Save JSON with readable formatting."""

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def build_review_decision(
    manifest,
    qa_report
):
    """Build a human-review decision."""

    job = manifest.get(
        "job",
        {}
    )

    skills = manifest.get(
        "skills",
        {}
    )

    validation = manifest.get(
        "validation",
        {}
    )

    qa_status = qa_report.get(
        "status",
        "UNKNOWN"
    )

    errors = qa_report.get(
        "errors",
        []
    )

    warnings = qa_report.get(
        "warnings",
        []
    )

    human_review_required = qa_report.get(
        "human_review_required",
        True
    )

    automatic_submission = qa_report.get(
        "automatic_submission",
        False
    )

    # ---------------------------------------------------------
    # Determine recommendation
    # ---------------------------------------------------------

    if errors:

        recommendation = "BLOCKED"

        reason = (
            "Application package contains errors. "
            "Human review and correction are required "
            "before submission."
        )

    elif qa_status == "QA_FAILED":

        recommendation = "BLOCKED"

        reason = (
            "Application QA failed. "
            "The package must be corrected before submission."
        )

    elif warnings:

        recommendation = "REVIEW_REQUIRED"

        reason = (
            "Application package passed QA with warnings. "
            "Human review is required before submission."
        )

    else:

        recommendation = (
            "READY_FOR_HUMAN_APPROVAL"
        )

        reason = (
            "Application package passed QA "
            "without warnings. Human approval is "
            "still required before submission."
        )

    # ---------------------------------------------------------
    # Required skill information
    # ---------------------------------------------------------

    matched_required = skills.get(
        "matched_required",
        []
    )

    required_gaps = skills.get(
        "required_gaps",
        []
    )

    matched_preferred = skills.get(
        "matched_preferred",
        []
    )

    preferred_gaps = skills.get(
        "preferred_gaps",
        []
    )

    # ---------------------------------------------------------
    # Human review checklist
    # ---------------------------------------------------------

    review_checklist = [
        {
            "item": "Confirm job title and company",
            "completed": False
        },
        {
            "item": "Confirm job location and work mode",
            "completed": False
        },
        {
            "item": "Review ATS resume PDF",
            "completed": False
        },
        {
            "item": "Review cover letter PDF",
            "completed": False
        },
        {
            "item": "Confirm contact information",
            "completed": False
        },
        {
            "item": "Confirm required skills are represented accurately",
            "completed": False
        },
        {
            "item": "Review required skill gaps",
            "completed": False
        },
        {
            "item": "Review preferred skill gaps",
            "completed": False
        },
        {
            "item": "Confirm all experience claims are truthful",
            "completed": False
        },
        {
            "item": "Confirm all education claims are truthful",
            "completed": False
        },
        {
            "item": "Confirm application deadline",
            "completed": False
        },
        {
            "item": "Confirm application portal and submission instructions",
            "completed": False
        },
        {
            "item": "Submit manually only after final approval",
            "completed": False
        }
    ]

    # ---------------------------------------------------------
    # Safety
    # ---------------------------------------------------------

    safety = {
        "human_review_required": True,
        "automatic_submission": False,
        "automatic_application": False,
        "automatic_email": False,
        "automatic_job_submission": False
    }

    # ---------------------------------------------------------
    # Final decision object
    # ---------------------------------------------------------

    decision = {

        "review_version": "1.0",

        "timestamp": datetime.now().isoformat(),

        "review_status": recommendation,

        "reason": reason,

        "job": {
            "job_id": job.get(
                "job_id",
                JOB_ID
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

        "qa": {
            "status": qa_status,
            "errors": errors,
            "warnings": warnings
        },

        "skills": {

            "matched_required": matched_required,

            "required_gaps": required_gaps,

            "matched_preferred": matched_preferred,

            "preferred_gaps": preferred_gaps
        },

        "validation": {
            "manifest_status": validation.get(
                "status",
                ""
            ),
            "manifest_errors": validation.get(
                "errors",
                []
            ),
            "manifest_warnings": validation.get(
                "warnings",
                []
            )
        },

        "human_review": {
            "required": human_review_required,
            "approved": False,
            "approved_by_human": False,
            "approval_timestamp": None,
            "reviewer": None
        },

        "safety": safety,

        "review_checklist": review_checklist,

        "next_action": (
            "Human must review the application package "
            "and manually approve it before submission."
        )
    }

    return decision


def print_review_decision(decision):
    """Print review decision to the terminal."""

    job = decision.get(
        "job",
        {}
    )

    qa = decision.get(
        "qa",
        {}
    )

    skills = decision.get(
        "skills",
        {}
    )

    human_review = decision.get(
        "human_review",
        {}
    )

    safety = decision.get(
        "safety",
        {}
    )

    print()

    print(
        "APPLICATION REVIEW AGENT"
    )

    print(
        "=" * 65
    )

    print()

    print(
        f"Job:      {job.get('title', '')}"
    )

    print(
        f"Company:  {job.get('company', '')}"
    )

    print(
        f"Location: {job.get('location', '')}"
    )

    print()

    print(
        "REVIEW STATUS"
    )

    print(
        f"  {decision.get('review_status', '')}"
    )

    print()

    print(
        "REASON"
    )

    print(
        f"  {decision.get('reason', '')}"
    )

    print()

    print(
        "QA STATUS"
    )

    print(
        f"  {qa.get('status', '')}"
    )

    print()

    print(
        "MATCHED REQUIRED SKILLS"
    )

    matched_required = skills.get(
        "matched_required",
        []
    )

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

    required_gaps = skills.get(
        "required_gaps",
        []
    )

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
        "PREFERRED SKILL GAPS"
    )

    preferred_gaps = skills.get(
        "preferred_gaps",
        []
    )

    if preferred_gaps:

        for skill in preferred_gaps:

            print(
                f"  GAP: {skill}"
            )

    else:

        print(
            "  None"
        )

    print()

    print(
        "QA WARNINGS"
    )

    warnings = qa.get(
        "warnings",
        []
    )

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
        "QA ERRORS"
    )

    errors = qa.get(
        "errors",
        []
    )

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
        f"  Required: "
        f"{human_review.get('required', True)}"
    )

    print(
        f"  Approved: "
        f"{human_review.get('approved', False)}"
    )

    print(
        f"  Approved by human: "
        f"{human_review.get('approved_by_human', False)}"
    )

    print()

    print(
        "SAFETY"
    )

    print(
        f"  Automatic submission: "
        f"{safety.get('automatic_submission', False)}"
    )

    print(
        f"  Automatic application: "
        f"{safety.get('automatic_application', False)}"
    )

    print(
        f"  Automatic email: "
        f"{safety.get('automatic_email', False)}"
    )

    print(
        f"  Automatic job submission: "
        f"{safety.get('automatic_job_submission', False)}"
    )

    print()

    print(
        "NEXT ACTION"
    )

    print(
        f"  {decision.get('next_action', '')}"
    )


def main():

    print()

    print(
        "APPLICATION REVIEW AGENT TEST - VERSION 1"
    )

    print(
        "=" * 65
    )

    # ---------------------------------------------------------
    # Check package directory
    # ---------------------------------------------------------

    if not PACKAGE_DIR.exists():

        print()

        print(
            "ERROR: Application package directory not found:"
        )

        print(
            PACKAGE_DIR
        )

        return

    # ---------------------------------------------------------
    # Check application manifest
    # ---------------------------------------------------------

    if not APPLICATION_MANIFEST.exists():

        print()

        print(
            "ERROR: Application manifest not found:"
        )

        print(
            APPLICATION_MANIFEST
        )

        return

    # ---------------------------------------------------------
    # Check QA report
    # ---------------------------------------------------------

    if not QA_REPORT.exists():

        print()

        print(
            "ERROR: QA report not found:"
        )

        print(
            QA_REPORT
        )

        return

    # ---------------------------------------------------------
    # Load files
    # ---------------------------------------------------------

    manifest = load_json(
        APPLICATION_MANIFEST
    )

    qa_report = load_json(
        QA_REPORT
    )

    # ---------------------------------------------------------
    # Build decision
    # ---------------------------------------------------------

    decision = build_review_decision(
        manifest,
        qa_report
    )

    # ---------------------------------------------------------
    # Print result
    # ---------------------------------------------------------

    print_review_decision(
        decision
    )

    # ---------------------------------------------------------
    # Save result
    # ---------------------------------------------------------

    save_json(
        REVIEW_DECISION,
        decision
    )

    print()

    print(
        "REVIEW DECISION SAVED:"
    )

    print(
        REVIEW_DECISION
    )

    print()

    print(
        "APPLICATION REVIEW COMPLETE"
    )

    print(
        "=" * 65
    )


if __name__ == "__main__":
    main()
