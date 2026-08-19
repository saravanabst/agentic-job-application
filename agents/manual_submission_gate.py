import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = "job_001"

sys.path.insert(
    0,
    str(BASE_DIR / "agents")
)


# ============================================================
# APPLICATION TRACKER
# ============================================================

from application_tracker import (
    initialize_database,
    get_application,
    update_status,
)


# ============================================================
# DISPLAY
# ============================================================

def print_header(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_application(application):

    print()

    print("APPLICATION")
    print("-" * 70)

    print(
        f"Job ID              : "
        f"{application.get('job_id', '')}"
    )

    print(
        f"Company             : "
        f"{application.get('company', '')}"
    )

    print(
        f"Job Title           : "
        f"{application.get('job_title', '')}"
    )

    print(
        f"Location            : "
        f"{application.get('location', '')}"
    )

    print(
        f"Work Mode           : "
        f"{application.get('work_mode', '')}"
    )

    print(
        f"Match Score         : "
        f"{application.get('match_score', '')}"
    )

    print(
        f"Decision            : "
        f"{application.get('decision', '')}"
    )

    print(
        f"Current Status      : "
        f"{application.get('application_status', '')}"
    )

    print(
        f"Human Approved      : "
        f"{bool(application.get('human_approved', False))}"
    )

    print(
        f"Reviewer            : "
        f"{application.get('reviewer')}"
    )

    print(
        f"Approved At         : "
        f"{application.get('approved_at')}"
    )

    print(
        f"Deadline            : "
        f"{application.get('application_deadline')}"
    )

    print(
        f"Deadline Status     : "
        f"{application.get('deadline_status')}"
    )

    print(
        f"Days Remaining      : "
        f"{application.get('days_remaining')}"
    )


# ============================================================
# VALIDATION
# ============================================================

# ============================================================
# VALIDATION
# ============================================================

def validate_submission(application):
    """
    Validate whether an application is eligible for
    manual submission confirmation.

    Rules:

        1. Application must exist.
        2. Application must NOT already be submitted.
        3. Explicit human approval is required.
        4. Application status must be approved.
        5. Expired or invalid deadlines block submission.

    Important:
        This function does NOT submit anything.
        It only validates whether manual submission
        confirmation is allowed.
    """

    errors = []

    # --------------------------------------------------------
    # Application existence
    # --------------------------------------------------------

    if not application:

        errors.append(
            "Application does not exist."
        )

        return errors

    status = application.get(
        "application_status"
    )

    human_approved = bool(
        application.get(
            "human_approved",
            False
        )
    )

    deadline_status = application.get(
        "deadline_status"
    )

    # --------------------------------------------------------
    # ALREADY SUBMITTED
    #
    # This check must return immediately.
    #
    # There is no reason to continue checking whether
    # the application is approved because a submitted
    # application must not be submitted again.
    # --------------------------------------------------------

    if status == "submitted":

        errors.append(
            "Application has already been submitted."
        )

        return errors

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    if not human_approved:

        errors.append(
            "Explicit human approval is required."
        )

    # --------------------------------------------------------
    # VALID APPLICATION STATUS
    # --------------------------------------------------------

    if status != "approved":

        errors.append(
            f"Application must have status "
            f"'approved' before manual submission. "
            f"Current status: '{status}'."
        )

    # --------------------------------------------------------
    # DEADLINE SAFETY
    #
    # Current application_tracker.py uses:
    #
    #     OVERDUE
    #     DUE_TODAY
    #     DUE_SOON
    #     UPCOMING
    #     NO_DEADLINE
    #     INVALID_DEADLINE
    #
    # Only OVERDUE and INVALID_DEADLINE block
    # manual submission.
    # --------------------------------------------------------

    if deadline_status in (
        "EXPIRED",
        "INVALID_DEADLINE"
    ):

        errors.append(
            f"Submission blocked because deadline "
            f"status is '{deadline_status}'."
        )

    return errors

# ============================================================
# MANUAL SUBMISSION
# ============================================================

def manual_submission_gate(job_id):

    print_header(
        "MANUAL APPLICATION SUBMISSION GATE"
    )

    application = get_application(
        job_id
    )

    if not application:

        print()

        print(
            f"ERROR: Application not found: {job_id}"
        )

        return False

    print_application(
        application
    )

    errors = validate_submission(
        application
    )

    if errors:

        print()

        print(
            "SUBMISSION BLOCKED"
        )

        print(
            "-" * 70
        )

        for error in errors:

            print(
                f"  ERROR: {error}"
            )

        print()

        print(
            "No database status was changed."
        )

        return False

    # --------------------------------------------------------
    # Safety warning
    # --------------------------------------------------------

    print()

    print(
        "IMPORTANT SAFETY CHECK"
    )

    print(
        "-" * 70
    )

    print(
        "This gate does NOT open a browser."
    )

    print(
        "This gate does NOT submit an online form."
    )

    print(
        "This gate does NOT send email."
    )

    print(
        "This gate does NOT automatically apply."
    )

    print()

    print(
        "You must manually submit the application "
        "through the employer's application portal."
    )

    print()

    print(
        f"Current database status: "
        f"{application.get('application_status')}"
    )

    print(
        f"Human approved: "
        f"{bool(application.get('human_approved'))}"
    )

    print(
        f"Deadline status: "
        f"{application.get('deadline_status')}"
    )

    print()

    response = input(
        "Have you manually submitted this application? [y/N]: "
    ).strip().lower()

    if response not in (
        "y",
        "yes"
    ):

        print()

        print(
            "SUBMISSION NOT RECORDED"
        )

        print(
            "Application remains in approved state."
        )

        return False

    # --------------------------------------------------------
    # Explicit confirmation
    # --------------------------------------------------------

    print()

    confirmation = input(
        "Type SUBMITTED to confirm: "
    ).strip()

    if confirmation != "SUBMITTED":

        print()

        print(
            "SUBMISSION NOT RECORDED"
        )

        print(
            "Confirmation text did not match."
        )

        return False

    # --------------------------------------------------------
    # Update tracker
    # --------------------------------------------------------

    print()

    print(
        "Recording manual submission..."
    )

    result = update_status(
        job_id,
        "submitted"
    )

    if not result:

        print()

        print(
            "SUBMISSION RECORDING FAILED"
        )

        return False

    # --------------------------------------------------------
    # Verify database
    # --------------------------------------------------------

    updated = get_application(
        job_id
    )

    if not updated:

        print()

        print(
            "SAFETY FAILURE"
        )

        print(
            "Application could not be reloaded."
        )

        return False

    final_status = updated.get(
        "application_status"
    )

    submitted_at = updated.get(
        "submitted_at"
    )

    if final_status != "submitted":

        print()

        print(
            "SAFETY FAILURE"
        )

        print(
            f"Expected status: submitted"
        )

        print(
            f"Actual status:   {final_status}"
        )

        return False

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print_header(
        "MANUAL SUBMISSION RECORDED"
    )

    print(
        f"Job ID:          {job_id}"
    )

    print(
        f"Status:          {final_status}"
    )

    print(
        f"Human Approved:  "
        f"{bool(updated.get('human_approved'))}"
    )

    print(
        f"Reviewer:        "
        f"{updated.get('reviewer')}"
    )

    print(
        f"Submitted At:    "
        f"{submitted_at}"
    )

    print()

    print(
        "SAFETY STATUS"
    )

    print(
        "  Automatic submission: False"
    )

    print(
        "  Automatic application: False"
    )

    print(
        "  Automatic email: False"
    )

    print(
        "  Automatic job submission: False"
    )

    print()

    print(
        "NEXT ACTION:"
    )

    print(
        "  Application follow-up tracking."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "MANUAL SUBMISSION GATE - VERSION 1"
    )

    print(
        "=" * 70
    )

    print()

    print(
        "Database:"
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
    # Run gate
    # --------------------------------------------------------

    result = manual_submission_gate(
        JOB_ID
    )

    print()

    print_header(
        "MANUAL SUBMISSION GATE COMPLETE"
    )

    if result:

        print(
            "RESULT: SUBMISSION RECORDED"
        )

        print()

        print(
            "The application was manually confirmed "
            "as submitted."
        )

    else:

        print(
            "RESULT: SUBMISSION NOT RECORDED"
        )

        print()

        print(
            "No automatic submission occurred."
        )


if __name__ == "__main__":

    main()
