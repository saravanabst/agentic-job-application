import sys
from pathlib import Path


# ============================================================
# TEST CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(
    0,
    str(BASE_DIR / "agents")
)


# ============================================================
# IMPORT MODULE UNDER TEST
# ============================================================

from employer_response import (
    classify_response,
    explain_classification,
    analyze_response,
)


# ============================================================
# INTERVIEW TEST
# ============================================================

def test_interview_response():

    response = (
        "We would like to invite you "
        "to an interview with our hiring manager."
    )

    result = analyze_response(
        response
    )

    assert result["category"] == "interview"

    assert result["recommended_status"] == "interview"

    assert result["human_action_required"] is True


# ============================================================
# REJECTION TEST
# ============================================================

def test_rejection_response():

    response = (
        "Unfortunately, we have decided "
        "not to proceed with your application."
    )

    result = analyze_response(
        response
    )

    assert result["category"] == "rejected"

    assert result["recommended_status"] == "rejected"

    assert result["human_action_required"] is True


# ============================================================
# OFFER TEST
# ============================================================

def test_offer_response():

    response = (
        "We are pleased to offer you "
        "the Data Analyst position."
    )

    result = analyze_response(
        response
    )

    assert result["category"] == "offer"

    assert result["recommended_status"] == "offer"

    assert result["human_action_required"] is True


# ============================================================
# UNKNOWN RESPONSE TEST
# ============================================================

def test_unknown_response():

    response = (
        "Thank you for your application. "
        "We will contact you soon."
    )

    result = analyze_response(
        response
    )

    assert result["category"] == "other"

    assert result["recommended_status"] is None

    assert result["human_action_required"] is True


# ============================================================
# CASE INSENSITIVITY TEST
# ============================================================

def test_response_is_case_insensitive():

    response = (
        "WE WOULD LIKE TO INVITE YOU "
        "TO AN INTERVIEW."
    )

    assert (
        classify_response(response)
        == "interview"
    )


# ============================================================
# EMPTY RESPONSE TEST
# ============================================================

def test_empty_response():

    result = analyze_response("")

    assert result["category"] == "other"

    assert result["recommended_status"] is None


# ============================================================
# CLASSIFICATION EXPLANATION TEST
# ============================================================

def test_classification_explanation():

    response = (
        "We would like to invite you "
        "to a technical interview."
    )

    result = explain_classification(
        response
    )

    assert result["category"] == "interview"

    assert result["matched_keyword"] is not None

    assert "interview" in result["reason"].lower()