import sys
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

PACKAGE_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
    / "application_package"
)

REVIEW_DECISION_FILE = (
    PACKAGE_DIR
    / "review_decision.json"
)


# ============================================================
# SAFE JSON FUNCTIONS
# ============================================================

def load_json(file_path):
    """
    Load a JSON file safely.
    """

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ============================================================
# IMPORT APPLICATION TRACKER
# ------------------------------------------------------------
sys.path.insert(0, str(BASE_DIR / 'agents'))
# ============================================================

from application_tracker import (
    initialize_database,
    get_application,
    set_human_approval,
    update_status,
)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_header(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_review_summary(review):

    job = review.get(
        "job",
        {}
    )

    qa = review.get(
        "qa",
        {}
    )

    skills = review.get(
        "skills",
        {}
    )

    safety = review.get(
        "safety",
        {}
    )

    print()

    print(
        f"Job ID:       "
        f"{job.get('job_id', JOB_ID)}"
    )

    print(
        f"Job Title:    "
        f"{job.get('title', '')}"
    )

    print(
        f"Company:      "
        f"{job.get('company', '')}"
    )

    print(
        f"Location:     "
        f"{job.get('location', '')}"
    )

    print(
        f"Work Mode:    "
        f"{job.get('work_mode', '')}"
    )

    print()

    print(
        f"Review Status: "
        f"{review.get('review_status', '')}"
    )

    print(
        f"QA Status:     "
        f"{qa.get('status', '')}"
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
        "IMPORTANT:"
    )

    print(
        "  Approval here does NOT submit the application."
    )

    print(
        "  Submission must remain a separate manual action."
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_review_decision(review):

    errors = []

    review_status = review.get(
        "review_status"
    )

    qa = review.get(
        "qa",
        {}
    )

    skills = review.get(
        "skills",
        {}
    )

    safety = review.get(
        "safety",
        {}
    )

    required_gaps = skills.get(
        "required_gaps",
        []
    )

    qa_errors = qa.get(
        "errors",
        []
    )

    # --------------------------------------------------------
    # Review status
    # --------------------------------------------------------

    if review_status not in (
        "REVIEW_REQUIRED",
        "READY_FOR_HUMAN_APPROVAL"
    ):

        errors.append(
            "Application is not in a valid human-review state."
        )

    # --------------------------------------------------------
    # QA errors
    # --------------------------------------------------------

    if qa_errors:

        errors.append(
            "QA errors are present. "
            "Application cannot be approved."
        )

    # --------------------------------------------------------
    # Required skill gaps
    #
    # Required skill gaps are presented to the human reviewer.
    # They do not automatically block approval.
    # The human reviewer decides whether the gap is acceptable.
    # --------------------------------------------------------

    required_gaps = skills.get(
    	"required_gaps",
    	[]
    )

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if safety.get(
        "automatic_submission",
        False
    ):

        errors.append(
            "Automatic submission must be disabled."
        )

    if safety.get(
        "automatic_application",
        False
    ):

        errors.append(
            "Automatic application must be disabled."
        )

    if safety.get(
        "automatic_email",
        False
    ):

        errors.append(
            "Automatic email must be disabled."
        )

    if safety.get(
        "automatic_job_submission",
        False
    ):

        errors.append(
            "Automatic job submission must be disabled."
        )

    return errors


# ============================================================
# TRACKER VALIDATION
# ============================================================

def validate_tracker_application(job_id):

    application = get_application(
        job_id
    )

    if not application:

        return None, [
            f"Application {job_id} does not exist "
            "in the application tracker."
        ]

    errors = []

    status = application[
        "application_status"
    ]

    human_approved = bool(
        application[
            "human_approved"
        ]
    )

    # --------------------------------------------------------
    # Already approved
    # --------------------------------------------------------

    if human_approved:

        errors.append(
            "Application is already human approved."
        )

    # --------------------------------------------------------
    # Invalid status
    # --------------------------------------------------------

    if status != "application_prepared":

        errors.append(
            f"Application tracker status is "
            f"'{status}', which is not eligible "
            "for this approval gate."
        )

    return application, errors


# ============================================================
# HUMAN APPROVAL
# ============================================================

def request_human_approval(
    job_id,
    review
):

    print_header(
        "HUMAN APPROVAL GATE"
    )

    print_review_summary(
        review
    )

    tracker_application, tracker_errors = (
        validate_tracker_application(
            job_id
        )
    )

    if tracker_errors:

        print()

        print(
            "APPROVAL BLOCKED"
        )

        for error in tracker_errors:

            print(
                f"  ERROR: {error}"
            )

        return False

    validation_errors = (
        validate_review_decision(
            review
        )
    )

    if validation_errors:

        print()

        print(
            "APPROVAL BLOCKED"
        )

        for error in validation_errors:

            print(
                f"  ERROR: {error}"
            )

        return False

    print()

    print(
        "HUMAN REVIEW REQUIRED"
    )

    print(
        "-" * 70
    )

    print(
        "Review the resume, cover letter, job details,"
    )

    print(
        "skills, claims, deadline and application"
    )

    print(
        "instructions before approving."
    )

    print()

    print(
        "This action will ONLY record your approval."
    )

    print(
        "It will NOT submit the application."
    )

    print()

    reviewer = input(
        "Enter reviewer name: "
    ).strip()

    if not reviewer:

        print()

        print(
            "APPROVAL CANCELLED"
        )

        print(
            "Reviewer name is required."
        )

        return False

    print()

    response = input(
        "Approve this application? [y/N]: "
    ).strip().lower()

    if response not in (
        "y",
        "yes"
    ):

        print()

        print(
            "APPLICATION NOT APPROVED"
        )

        print(
            "Application remains in human review."
        )

        return False

    # --------------------------------------------------------
    # Explicit human approval
    # --------------------------------------------------------

    print()

    print(
        "Recording explicit human approval..."
    )

    result = set_human_approval(
        job_id,
        True,
        reviewer
    )

    if not result:

        print()

        print(
            "APPROVAL FAILED"
        )

        return False

    # STATUS TRANSITION
    # update_status() is the single authority for application status.

    status_updated = update_status(
        job_id,
        "approved"
    )

    if not status_updated:

        print()

        print(
            "STATUS TRANSITION FAILED"
        )

        print(
            "Rolling back human approval."
        )

        rollback = set_human_approval(
            job_id,
            False
        )

        if not rollback:

            print()

            print(
                "CRITICAL SAFETY FAILURE"
            )

            print(
                "Human approval rollback failed."
            )

        return False

    # --------------------------------------------------------
    # Verify database state
    # --------------------------------------------------------

    updated_application = get_application(
        job_id
    )

    if not updated_application:

        print()

        print(
            "ERROR: Application disappeared "
            "from tracker."
        )

        return False

    final_status = updated_application[
        "application_status"
    ]

    final_human_approved = bool(
        updated_application[
            "human_approved"
        ]
    )

    final_reviewer = updated_application[
        "reviewer"
    ]

    approved_at = updated_application[
        "approved_at"
    ]

    # --------------------------------------------------------
    # Final safety verification
    # --------------------------------------------------------

    if not final_human_approved:

        print()

        print(
            "SAFETY FAILURE:"
        )

        print(
            "Human approval was not recorded."
        )

        return False

    if final_status != "approved":

        print()

        print(
            "SAFETY FAILURE:"
        )

        print(
            f"Expected status: approved"
        )

        print(
            f"Actual status:   {final_status}"
        )

        return False

    print()

    print(
        "HUMAN APPROVAL SUCCESSFUL"
    )

    print(
        "=" * 70
    )

    print(
        f"Job ID:          {job_id}"
    )

    print(
        f"Status:          {final_status}"
    )

    print(
        f"Human Approved:  {final_human_approved}"
    )

    print(
        f"Reviewer:        {final_reviewer}"
    )

    print(
        f"Approved At:     {approved_at}"
    )

    print()

    print(
        "SAFETY STOP"
    )

    print(
        "  Automatic submission: BLOCKED"
    )

    print(
        "  Automatic application: BLOCKED"
    )

    print(
        "  Automatic email: BLOCKED"
    )

    print(
        "  Automatic job submission: BLOCKED"
    )

    print()

    print(
        "NEXT ACTION:"
    )

    print(
        "  Human must manually submit the application."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "HUMAN APPROVAL GATE TEST - VERSION 1"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "DATABASE:"
    )

    print(
        BASE_DIR
        / "applications"
        / "data"
        / "applications.db"
    )

    # --------------------------------------------------------
    # Initialize database
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Check review decision
    # --------------------------------------------------------

    if not REVIEW_DECISION_FILE.exists():

        print()

        print(
            "ERROR: Review decision not found:"
        )

        print(
            REVIEW_DECISION_FILE
        )

        print()

        print(
            "Run first:"
        )

        print(
            "python agents\\application_review.py"
        )

        return

    # --------------------------------------------------------
    # Load review decision
    # --------------------------------------------------------

    try:

        review = load_json(
            REVIEW_DECISION_FILE
        )

    except json.JSONDecodeError as error:

        print()

        print(
            "ERROR: Invalid review_decision.json"
        )

        print(
            error
        )

        return

    except OSError as error:

        print()

        print(
            "ERROR: Could not read review decision."
        )

        print(
            error
        )

        return

    # --------------------------------------------------------
    # Check job ID
    # --------------------------------------------------------

    review_job_id = review.get(
        "job",
        {}
    ).get(
        "job_id",
        JOB_ID
    )

    if review_job_id != JOB_ID:

        print()

        print(
            "ERROR: Job ID mismatch."
        )

        print(
            f"Expected: {JOB_ID}"
        )

        print(
            f"Found:    {review_job_id}"
        )

        return

    # --------------------------------------------------------
    # Request human approval
    # --------------------------------------------------------

    approved = request_human_approval(
        JOB_ID,
        review
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()

    print_header(
        "HUMAN APPROVAL GATE COMPLETE"
    )

    if approved:

        print(
            "RESULT: APPROVED BY HUMAN"
        )

        print()

        print(
            "The application is approved in the tracker."
        )

        print(
            "No application has been submitted."
        )

    else:

        print(
            "RESULT: NOT APPROVED"
        )

        print()

        print(
            "The application remains under human review."
        )

        print(
            "No application has been submitted."
        )


if __name__ == "__main__":

    main()
