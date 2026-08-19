import sys
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

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
# ALLOWED FOLLOW-UP STATUSES
# ============================================================

FOLLOWUP_STATUSES = {
    "submitted",

    "interview",
    "rejected",
    "offer",
    "withdrawn"
}


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_header(title):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def print_application(application):

    print()

    print(
        "APPLICATION"
    )

    print(
        "-" * 70
    )

    fields = [
        ("Job ID", "job_id"),
        ("Company", "company"),
        ("Job Title", "job_title"),
        ("Location", "location"),
        ("Work Mode", "work_mode"),
        ("Match Score", "match_score"),
        ("Decision", "decision"),
        ("Status", "application_status"),
        ("Human Approved", "human_approved"),
        ("Reviewer", "reviewer"),
        ("Approved At", "approved_at"),
        ("Submitted At", "submitted_at"),
        ("Deadline", "application_deadline"),
        ("Deadline Status", "deadline_status"),
        ("Days Remaining", "days_remaining"),
        ("Notes", "notes"),
    ]

    for label, key in fields:

        value = application.get(
            key
        )

        if key == "human_approved":

            value = bool(value)

        print(
            f"{label:20}: {value}"
        )

    print()


# ============================================================
# VALIDATE APPLICATION
# ============================================================

def validate_application(
    application
):

    errors = []

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
            0
        )
    )

    # --------------------------------------------------------
    # Human approval
    # --------------------------------------------------------

    if not human_approved:

        errors.append(
            "Application has not been approved by a human."
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    if status not in FOLLOWUP_STATUSES:

        errors.append(
            f"Current status '{status}' is not a "
            "valid follow-up status."
        )

    return errors


# ============================================================
# STATUS DESCRIPTION
# ============================================================

def describe_status(status):

    descriptions = {

        "submitted":
            "Application has been manually submitted.",


        "interview":
            "Candidate has been invited to interview.",

        "rejected":
            "Application was rejected or unsuccessful.",

        "offer":
            "Employer has made an offer.",

        "withdrawn":
            "Application was withdrawn."
    }

    return descriptions.get(
        status,
        "Unknown status."
    )


# ============================================================
# STATUS UPDATE
# ============================================================

def update_application_status(
    job_id,
    new_status
):

    application = get_application(
        job_id
    )

    if not application:

        print()

        print(
            "ERROR: Application not found."
        )

        return False

    current_status = application.get(
        "application_status"
    )

    human_approved = bool(
        application.get(
            "human_approved",
            0
        )
    )

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

    if not human_approved:

        print()

        print(
            "UPDATE BLOCKED"
        )

        print(
            "Human approval is required."
        )

        return False

    # --------------------------------------------------------
    # Validate target status
    # --------------------------------------------------------

    if new_status not in FOLLOWUP_STATUSES:

        print()

        print(
            "INVALID STATUS"
        )

        print(
            f"Allowed statuses:"
        )

        for status in sorted(
            FOLLOWUP_STATUSES
        ):

            print(
                f"  {status}"
            )

        return False

    # --------------------------------------------------------
    # Prevent meaningless update
    # --------------------------------------------------------

    if current_status == new_status:

        print()

        print(
            "NO CHANGE"
        )

        print(
            f"Application is already '{new_status}'."
        )

        return False

    # --------------------------------------------------------
    # Submission protection
    # --------------------------------------------------------

    if new_status == "submitted":

        if current_status != "approved":

            print()

            print(
                "SUBMISSION STATUS BLOCKED"
            )

            print(
                "The application must first be "
                "approved by a human."
            )

            return False

        print()

        print(
            "IMPORTANT:"
        )

        print(
            "This status does NOT submit the application."
        )

        print(
            "The employer portal submission must "
            "already have happened manually."
        )

        confirmation = input(
            "Confirm manual submission already occurred? [y/N]: "
        ).strip().lower()

        if confirmation not in (
            "y",
            "yes"
        ):

            print()

            print(
                "STATUS UPDATE CANCELLED"
            )

            return False

    # --------------------------------------------------------
    # Update
    # --------------------------------------------------------

    print()

    print(
        f"Updating:"
    )

    print(
        f"  {current_status} -> {new_status}"
    )

    result = update_status(
        job_id,
        new_status
    )

    if not result:

        print()

        print(
            "STATUS UPDATE FAILED"
        )

        return False

    # --------------------------------------------------------
    # Verify
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

    if final_status != new_status:

        print()

        print(
            "SAFETY FAILURE"
        )

        print(
            f"Expected: {new_status}"
        )

        print(
            f"Actual:   {final_status}"
        )

        return False

    # --------------------------------------------------------
    # Success
    # --------------------------------------------------------

    print()

    print_header(
        "STATUS UPDATE SUCCESSFUL"
    )

    print(
        f"Job ID:       {job_id}"
    )

    print(
        f"Previous:     {current_status}"
    )

    print(
        f"Current:      {final_status}"
    )

    print(
        f"Meaning:      {describe_status(final_status)}"
    )

    print(
        f"Updated At:   "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )

    return True


# ============================================================
# INTERACTIVE FOLLOW-UP
# ============================================================

def run_followup(
    job_id
):

    print_header(
        "APPLICATION FOLLOW-UP AGENT"
    )

    application = get_application(
        job_id
    )

    if not application:

        print()

        print(
            f"Application not found: {job_id}"
        )

        return False

    print_application(
        application
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    validation_errors = validate_application(
        application
    )

    if validation_errors:

        print_header(
            "FOLLOW-UP BLOCKED"
        )

        for error in validation_errors:

            print(
                f"ERROR: {error}"
            )

        return False

    current_status = application.get(
        "application_status"
    )

    print_header(
        "CURRENT STATUS"
    )

    print(
        f"Current status: {current_status}"
    )

    print(
        describe_status(
            current_status
        )
    )

    print()

    print(
        "AVAILABLE FOLLOW-UP STATUSES"
    )

    print(
        "-" * 70
    )

    for status in sorted(
        FOLLOWUP_STATUSES
    ):

        print(
            f"  {status:15} "
            f"- {describe_status(status)}"
        )

    print()

    new_status = input(
        "Enter new status, or press Enter to cancel: "
    ).strip().lower()

    if not new_status:

        print()

        print(
            "FOLLOW-UP CANCELLED"
        )

        return False

    return update_application_status(
        job_id,
        new_status
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        f"APPLICATION FOLLOW-UP AGENT - "
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

    print()

    # --------------------------------------------------------
    # Initialize
    # --------------------------------------------------------

    initialize_database()

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    result = run_followup(
        JOB_ID
    )

    # --------------------------------------------------------
    # Final
    # --------------------------------------------------------

    print()

    print_header(
        "APPLICATION FOLLOW-UP COMPLETE"
    )

    if result:

        print(
            "RESULT: STATUS UPDATED"
        )

    else:

        print(
            "RESULT: NO STATUS UPDATE"
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


if __name__ == "__main__":

    main()
