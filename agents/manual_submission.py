import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = "job_001"

PIPELINE_VERSION = "VERSION 1"


# ============================================================
# IMPORT APPLICATION TRACKER
# ============================================================

sys.path.insert(
    0,
    str(BASE_DIR / "agents")
)

from application_tracker import (
    initialize_database,
    get_application,
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


def print_application(application):

    if not application:

        return

    print()

    print(
        "APPLICATION DETAILS"
    )

    print(
        "-" * 70
    )

    print(
        f"Job ID:              "
        f"{application.get('job_id', '')}"
    )

    print(
        f"Company:             "
        f"{application.get('company', '')}"
    )

    print(
        f"Job Title:           "
        f"{application.get('job_title', '')}"
    )

    print(
        f"Location:            "
        f"{application.get('location', '')}"
    )

    print(
        f"Work Mode:           "
        f"{application.get('work_mode', '')}"
    )

    print(
        f"Match Score:         "
        f"{application.get('match_score', '')}"
    )

    print(
        f"Decision:            "
        f"{application.get('decision', '')}"
    )

    print(
        f"Application Status:  "
        f"{application.get('application_status', '')}"
    )

    print(
        f"Human Approved:      "
        f"{bool(application.get('human_approved', 0))}"
    )

    print(
        f"Reviewer:            "
        f"{application.get('reviewer')}"
    )

    print(
        f"Approved At:         "
        f"{application.get('approved_at')}"
    )

    print(
        f"Deadline:            "
        f"{application.get('application_deadline')}"
    )

    print(
        f"Deadline Status:     "
        f"{application.get('deadline_status')}"
    )

    print(
        f"Days Remaining:      "
        f"{application.get('days_remaining')}"
    )

    print()


# ============================================================
# VALIDATION
# ============================================================

def validate_submission_state(application):

    errors = []

    if not application:

        errors.append(
            "Application does not exist in tracker."
        )

        return errors

    status = application.get(
        "application_status"
    )

    human_approved = bool(
        application.get(
            "human_approved",
            0
        )
    )

    deadline_status = application.get(
        "deadline_status"
    )

    # --------------------------------------------------------
    # HUMAN APPROVAL
    # --------------------------------------------------------

    if not human_approved:

        errors.append(
            "Application has not been explicitly "
            "approved by a human."
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if status != "approved":

        errors.append(
            f"Application status is '{status}'. "
            "Only 'approved' applications can be "
            "recorded as submitted."
        )

    # --------------------------------------------------------
    # DEADLINE
    # --------------------------------------------------------

    if deadline_status in (
        "EXPIRED",
        "INVALID_DEADLINE"
    ):

        errors.append(
            f"Application cannot be submitted because "
            f"deadline status is '{deadline_status}'."
        )

    return errors


# ============================================================
# MANUAL SUBMISSION CONFIRMATION
# ============================================================

def request_manual_submission(
    job_id
):

    print_header(
        "MANUAL SUBMISSION RECORDER"
    )

    print(
        "IMPORTANT:"
    )

    print(
        "This program does NOT open the job portal."
    )

    print(
        "This program does NOT submit the application."
    )

    print(
        "You must manually submit the application "
        "on the employer's website."
    )

    print()

    # --------------------------------------------------------
    # Load application
    # --------------------------------------------------------

    application = get_application(
        job_id
    )

    if not application:

        print()

        print(
            "SUBMISSION BLOCKED"
        )

        print(
            f"Application not found: {job_id}"
        )

        return False

    # --------------------------------------------------------
    # Display application
    # --------------------------------------------------------

    print_application(
        application
    )

    # --------------------------------------------------------
    # Validate state
    # --------------------------------------------------------

    validation_errors = (
        validate_submission_state(
            application
        )
    )

    if validation_errors:

        print_header(
            "SUBMISSION BLOCKED"
        )

        for error in validation_errors:

            print(
                f"ERROR: {error}"
            )

        return False

    # --------------------------------------------------------
    # Safety checkpoint
    # --------------------------------------------------------

    print_header(
        "SAFETY CHECKPOINT"
    )

    print(
        "The tracker confirms:"
    )

    print(
        "  Human approval:        TRUE"
    )

    print(
        "  Application status:    APPROVED"
    )

    print(
        "  Deadline:              VALID"
    )

    print()

    print(
        "NO APPLICATION HAS BEEN SUBMITTED BY THIS PROGRAM."
    )

    print()

    print(
        "FIRST:"
    )

    print(
        "1. Open the employer's application portal."
    )

    print(
        "2. Review the job and application details."
    )

    print(
        "3. Upload the approved resume."
    )

    print(
        "4. Upload the approved cover letter."
    )

    print(
        "5. Complete the employer's application form."
    )

    print(
        "6. Review every answer."
    )

    print(
        "7. Manually click the employer's Submit button."
    )

    print()

    print(
        "ONLY AFTER YOU HAVE ACTUALLY SUBMITTED:"
    )

    print(
        "Return to this terminal and confirm the submission."
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
            "Application remains APPROVED."
        )

        print(
            "No tracker status was changed."
        )

        return False

    # --------------------------------------------------------
    # Final confirmation
    # --------------------------------------------------------

    print()

    print(
        "FINAL CONFIRMATION"
    )

    print(
        "-" * 70
    )

    print(
        "You are confirming that the application was "
        "actually submitted manually."
    )

    print()

    final_response = input(
        "Confirm manual submission was completed? [y/N]: "
    ).strip().lower()

    if final_response not in (
        "y",
        "yes"
    ):

        print()

        print(
            "SUBMISSION NOT RECORDED"
        )

        print(
            "Application remains APPROVED."
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

        print(
            "The application tracker was not changed."
        )

        return False

    # --------------------------------------------------------
    # Verify database
    # --------------------------------------------------------

    updated_application = get_application(
        job_id
    )

    if not updated_application:

        print()

        print(
            "SAFETY FAILURE"
        )

        print(
            "Application could not be reloaded."
        )

        return False

    final_status = updated_application.get(
        "application_status"
    )

    submitted_at = updated_application.get(
        "submitted_at"
    )

    human_approved = bool(
        updated_application.get(
            "human_approved",
            0
        )
    )

    # --------------------------------------------------------
    # Safety verification
    # --------------------------------------------------------

    if not human_approved:

        print()

        print(
            "SAFETY FAILURE"
        )

        print(
            "Human approval is no longer present."
        )

        return False

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
        f"Job ID:             {job_id}"
    )

    print(
        f"Final status:       {final_status}"
    )

    print(
        f"Human approved:     {human_approved}"
    )

    print(
        f"Submitted at:       {submitted_at}"
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "The application was submitted manually."
    )

    print(
        "The program only recorded the submission "
        "in the tracker."
    )

    print()

    print(
        "NEXT STAGE:"
    )

    print(
        "Application tracking / follow-up monitoring."
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        f"MANUAL SUBMISSION RECORDER - "
        f"{PIPELINE_VERSION}"
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
    # Execute manual submission workflow
    # --------------------------------------------------------

    result = request_manual_submission(
        JOB_ID
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print()

    print_header(
        "MANUAL SUBMISSION RECORDER COMPLETE"
    )

    if result:

        print(
            "RESULT: SUBMISSION RECORDED"
        )

        print()

        print(
            "The application tracker now records "
            "this application as SUBMITTED."
        )

    else:

        print(
            "RESULT: SUBMISSION NOT RECORDED"
        )

        print()

        print(
            "The application tracker was not changed."
        )


if __name__ == "__main__":

    main()