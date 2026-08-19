import sys
import json
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

AGENTS_DIR = BASE_DIR / "agents"

sys.path.insert(
    0,
    str(AGENTS_DIR)
)

JOB_ID = "job_001"


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


# ============================================================
# SAFETY CONSTANTS
# ============================================================

AUTOMATIC_SUBMISSION = False
AUTOMATIC_APPLICATION = False
AUTOMATIC_EMAIL = False
AUTOMATIC_JOB_SUBMISSION = False
HUMAN_APPROVAL_REQUIRED = True


# ============================================================
# IMPORT EXISTING MODULES
# ============================================================

from application_tracker import (
    initialize_database,
    get_application,
    application_exists,
)

from application_review import (
    load_json,
    save_json,
    build_review_decision,
    print_review_decision,
)

from human_approval_gate import (
    request_human_approval,
)


# ============================================================
# DISPLAY
# ============================================================

def print_header(title):

    print()
    print("=" * 75)
    print(title)
    print("=" * 75)


def print_safety_status():

    print()
    print("SAFETY STATUS")
    print("-" * 75)

    print(
        f"Automatic submission:       "
        f"{AUTOMATIC_SUBMISSION}"
    )

    print(
        f"Automatic application:      "
        f"{AUTOMATIC_APPLICATION}"
    )

    print(
        f"Automatic email:            "
        f"{AUTOMATIC_EMAIL}"
    )

    print(
        f"Automatic job submission:   "
        f"{AUTOMATIC_JOB_SUBMISSION}"
    )

    print(
        f"Human approval required:    "
        f"{HUMAN_APPROVAL_REQUIRED}"
    )


# ============================================================
# SAFETY VALIDATION
# ============================================================

def validate_global_safety():

    errors = []

    if AUTOMATIC_SUBMISSION:

        errors.append(
            "Automatic submission must remain disabled."
        )

    if AUTOMATIC_APPLICATION:

        errors.append(
            "Automatic application must remain disabled."
        )

    if AUTOMATIC_EMAIL:

        errors.append(
            "Automatic email must remain disabled."
        )

    if AUTOMATIC_JOB_SUBMISSION:

        errors.append(
            "Automatic job submission must remain disabled."
        )

    if not HUMAN_APPROVAL_REQUIRED:

        errors.append(
            "Human approval must remain mandatory."
        )

    return errors


# ============================================================
# FILE CHECKING
# ============================================================

def check_required_files():

    print_header(
        "STEP 1 - CHECK APPLICATION PACKAGE"
    )

    print(
        f"Job ID: {JOB_ID}"
    )

    print(
        f"Package directory:\n{PACKAGE_DIR}"
    )

    if not PACKAGE_DIR.exists():

        print()
        print(
            "ERROR: Application package directory "
            "does not exist."
        )

        return False

    required_files = [
        APPLICATION_MANIFEST,
        QA_REPORT,
    ]

    all_present = True

    for file_path in required_files:

        if file_path.exists():

            print(
                f"FOUND: {file_path.name}"
            )

        else:

            print(
                f"MISSING: {file_path.name}"
            )

            all_present = False

    return all_present


# ============================================================
# LOAD PACKAGE
# ============================================================

def load_application_package():

    print_header(
        "STEP 2 - LOAD APPLICATION PACKAGE"
    )

    try:

        manifest = load_json(
            APPLICATION_MANIFEST
        )

    except Exception as error:

        print(
            f"ERROR loading application manifest: "
            f"{error}"
        )

        return None, None

    try:

        qa_report = load_json(
            QA_REPORT
        )

    except Exception as error:

        print(
            f"ERROR loading QA report: "
            f"{error}"
        )

        return None, None

    print(
        "Application manifest loaded."
    )

    print(
        "QA report loaded."
    )

    return manifest, qa_report


# ============================================================
# VERIFY JOB
# ============================================================

def verify_job_id(manifest):

    print_header(
        "STEP 3 - VERIFY JOB"
    )

    job = manifest.get(
        "job",
        {}
    )

    manifest_job_id = job.get(
        "job_id"
    )

    print(
        f"Expected Job ID: {JOB_ID}"
    )

    print(
        f"Manifest Job ID: {manifest_job_id}"
    )

    if manifest_job_id != JOB_ID:

        print()
        print(
            "ERROR: Job ID mismatch."
        )

        return False

    print(
        "Job ID verified."
    )

    print(
        f"Title:    {job.get('title', '')}"
    )

    print(
        f"Company:  {job.get('company', '')}"
    )

    print(
        f"Location: {job.get('location', '')}"
    )

    print(
        f"Work Mode: {job.get('work_mode', '')}"
    )

    return True


# ============================================================
# QA CHECK
# ============================================================

def check_qa(qa_report):

    print_header(
        "STEP 4 - APPLICATION QA"
    )

    status = qa_report.get(
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

    print(
        f"QA Status: {status}"
    )

    print(
        f"QA Errors: {len(errors)}"
    )

    print(
        f"QA Warnings: {len(warnings)}"
    )

    if errors:

        print()
        print(
            "QA ERRORS"
        )

        for error in errors:

            print(
                f"  ERROR: {error}"
            )

        return False

    if status == "QA_FAILED":

        print()
        print(
            "QA FAILED."
        )

        return False

    print()
    print(
        "QA passed."
    )

    if warnings:

        print()
        print(
            "QA WARNINGS"
        )

        for warning in warnings:

            print(
                f"  WARNING: {warning}"
            )

    return True


# ============================================================
# BUILD REVIEW DECISION
# ============================================================

def create_review_decision(
    manifest,
    qa_report
):

    print_header(
        "STEP 5 - BUILD REVIEW DECISION"
    )

    decision = build_review_decision(
        manifest,
        qa_report
    )

    save_json(
        REVIEW_DECISION,
        decision
    )

    print(
        f"Review decision saved:"
    )

    print(
        REVIEW_DECISION
    )

    print_review_decision(
        decision
    )

    return decision


# ============================================================
# TRACKER CHECK
# ============================================================

def check_application_tracker():

    print_header(
        "STEP 6 - CHECK APPLICATION TRACKER"
    )

    application = get_application(
        JOB_ID
    )

    if not application:

        print(
            "ERROR: Application does not exist "
            "in the tracker."
        )

        print()
        print(
            "Run the job pipeline first."
        )

        return False

    print(
        f"Job ID:          "
        f"{application.get('job_id', '')}"
    )

    print(
        f"Company:         "
        f"{application.get('company', '')}"
    )

    print(
        f"Job Title:       "
        f"{application.get('job_title', '')}"
    )

    print(
        f"Application:     "
        f"{application.get('application_status', '')}"
    )

    print(
        f"Human Approved:  "
        f"{bool(application.get('human_approved', 0))}"
    )

    print(
        f"Reviewer:        "
        f"{application.get('reviewer')}"
    )

    print(
        f"Deadline:        "
        f"{application.get('application_deadline')}"
    )

    print(
        f"Deadline Status: "
        f"{application.get('deadline_status')}"
    )

    return True


# ============================================================
# HUMAN APPROVAL
# ============================================================

def run_human_approval():

    print_header(
        "STEP 7 - HUMAN APPROVAL GATE"
    )

    if not REVIEW_DECISION.exists():

        print(
            "ERROR: Review decision does not exist."
        )

        return False

    try:

        review = load_json(
            REVIEW_DECISION
        )

    except Exception as error:

        print(
            f"ERROR loading review decision: "
            f"{error}"
        )

        return False

    print(
        "The system is now waiting for explicit "
        "human approval."
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "Approval does NOT submit the application."
    )

    print(
        "Submission remains a separate manual action."
    )

    print()

    approved = request_human_approval(
        JOB_ID,
        review
    )

    return approved


# ============================================================
# FINAL STATUS
# ============================================================

def print_final_status(
    approved
):

    print_header(
        "STEP 8 - WORKFLOW COMPLETE"
    )

    application = get_application(
        JOB_ID
    )

    if application:

        status = application.get(
            "application_status"
        )

        human_approved = bool(
            application.get(
                "human_approved",
                0
            )
        )

        reviewer = application.get(
            "reviewer"
        )

        print(
            f"Job ID:          {JOB_ID}"
        )

        print(
            f"Application:     {status}"
        )

        print(
            f"Human Approved:  {human_approved}"
        )

        print(
            f"Reviewer:        {reviewer}"
        )

    print()

    if approved:

        print(
            "RESULT: HUMAN APPROVAL RECORDED"
        )

        print()

        print(
            "The application is approved in the tracker."
        )

        print(
            "NO APPLICATION HAS BEEN SUBMITTED."
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
            "NO APPLICATION HAS BEEN SUBMITTED."
        )

    print_safety_status()

    print()

    print(
        "FINAL ACTION:"
    )

    print(
        "Human must manually submit the application "
        "through the employer's application portal."
    )

    print()

    print(
        f"Completed at: "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )


# ============================================================
# MAIN WORKFLOW
# ============================================================

def main():

    print_header(
        "AGENTIC JOB APPLICATION WORKFLOW"
    )

    print(
        "Workflow Version: 1.0"
    )

    print(
        f"Job ID: {JOB_ID}"
    )

    print_safety_status()

    # --------------------------------------------------------
    # GLOBAL SAFETY CHECK
    # --------------------------------------------------------

    safety_errors = validate_global_safety()

    if safety_errors:

        print()
        print(
            "SAFETY VALIDATION FAILED"
        )

        for error in safety_errors:

            print(
                f"  ERROR: {error}"
            )

        return

    print()
    print(
        "Global safety validation passed."
    )

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    print_header(
        "DATABASE INITIALIZATION"
    )

    initialize_database()

    print(
        "Application database ready."
    )

    # --------------------------------------------------------
    # PACKAGE FILES
    # --------------------------------------------------------

    if not check_required_files():

        print()
        print(
            "WORKFLOW STOPPED."
        )

        return

    # --------------------------------------------------------
    # LOAD PACKAGE
    # --------------------------------------------------------

    manifest, qa_report = (
        load_application_package()
    )

    if manifest is None:

        print(
            "WORKFLOW STOPPED."
        )

        return

    # --------------------------------------------------------
    # JOB VALIDATION
    # --------------------------------------------------------

    if not verify_job_id(
        manifest
    ):

        print()
        print(
            "WORKFLOW STOPPED."
        )

        return

    # --------------------------------------------------------
    # QA
    # --------------------------------------------------------

    if not check_qa(
        qa_report
    ):

        print()
        print(
            "WORKFLOW STOPPED."
        )

        print(
            "Application package must be corrected "
            "before human approval."
        )

        return

    # --------------------------------------------------------
    # REVIEW DECISION
    # --------------------------------------------------------

    review = create_review_decision(
        manifest,
        qa_report
    )

    review_status = review.get(
        "review_status"
    )

    if review_status == "BLOCKED":

        print()
        print(
            "WORKFLOW STOPPED."
        )

        print(
            "Application review decision is BLOCKED."
        )

        return

    # --------------------------------------------------------
    # TRACKER
    # --------------------------------------------------------

    if not check_application_tracker():

        print()
        print(
            "WORKFLOW STOPPED."
        )

        return

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    approved = run_human_approval()

    # --------------------------------------------------------
    # FINAL STATUS
    # --------------------------------------------------------

    print_final_status(
        approved
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()