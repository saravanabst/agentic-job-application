# ============================================================
# EMPLOYER RESPONSE INTELLIGENCE AGENT
# ============================================================

"""
Classifies employer responses into a recommended outcome.

IMPORTANT:
This agent only makes a recommendation.

It does NOT:
- change application status
- modify the database
- send messages
- submit applications
- make irreversible decisions
"""


# ============================================================
# RESPONSE CATEGORIES
# ============================================================

RESPONSE_CATEGORIES = [
    "interview",
    "rejected",
    "offer",
    "other"
]


# ============================================================
# KEYWORDS
# ============================================================

INTERVIEW_KEYWORDS = [
    "interview",
    "interviewing",
    "phone screen",
    "phone screening",
    "video interview",
    "technical interview",
    "next round",
    "next stage",
    "meet with",
    "schedule a call",
    "schedule an interview",
]


REJECTION_KEYWORDS = [
    "unfortunately",
    "not moving forward",
    "not move forward",
    "decided not to proceed",
    "not proceeding",
    "another candidate",
    "other candidates",
    "unsuccessful",
    "rejected",
    "regret to inform",
]


OFFER_KEYWORDS = [
    "job offer",
    "offer letter",
    "pleased to offer",
    "offer you the position",
    "offer you the role",
    "employment offer",
    "we would like to offer",
]


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_response(response_text):
    """
    Classify an employer response.

    Returns one of:

        interview
        rejected
        offer
        other
    """

    if not isinstance(response_text, str):

        raise TypeError(
            "response_text must be a string."
        )

    text = response_text.strip().lower()

    if not text:

        return "other"

    # --------------------------------------------------------
    # OFFER
    # --------------------------------------------------------

    for keyword in OFFER_KEYWORDS:

        if keyword in text:

            return "offer"

    # --------------------------------------------------------
    # INTERVIEW
    # --------------------------------------------------------

    for keyword in INTERVIEW_KEYWORDS:

        if keyword in text:

            return "interview"

    # --------------------------------------------------------
    # REJECTION
    # --------------------------------------------------------

    for keyword in REJECTION_KEYWORDS:

        if keyword in text:

            return "rejected"

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    return "other"


# ============================================================
# CLASSIFICATION DETAILS
# ============================================================

def explain_classification(response_text):
    """
    Explain why an employer response was classified.

    Returns:
        category
        matched_keyword
        reason
    """

    if not isinstance(response_text, str):

        raise TypeError(
            "response_text must be a string."
        )

    text = response_text.strip().lower()

    if not text:

        return {
            "category": "other",
            "matched_keyword": None,
            "reason": "The employer response is empty."
        }

    # --------------------------------------------------------
    # OFFER
    # --------------------------------------------------------

    for keyword in OFFER_KEYWORDS:

        if keyword in text:

            return {
                "category": "offer",
                "matched_keyword": keyword,
                "reason":
                    "The response contains an offer-related phrase."
            }

    # --------------------------------------------------------
    # INTERVIEW
    # --------------------------------------------------------

    for keyword in INTERVIEW_KEYWORDS:

        if keyword in text:

            return {
                "category": "interview",
                "matched_keyword": keyword,
                "reason":
                    "The response contains an interview-related phrase."
            }

    # --------------------------------------------------------
    # REJECTION
    # --------------------------------------------------------

    for keyword in REJECTION_KEYWORDS:

        if keyword in text:

            return {
                "category": "rejected",
                "matched_keyword": keyword,
                "reason":
                    "The response contains a rejection-related phrase."
            }

    # --------------------------------------------------------
    # OTHER
    # --------------------------------------------------------

    return {
        "category": "other",
        "matched_keyword": None,
        "reason":
            "No known employer-response pattern was detected."
    }

# ============================================================
# RECOMMENDATION
# ============================================================

def get_recommendation(response_text):
    """
    Return a human-readable recommendation.

    This function does not update application status.
    """

    category = classify_response(
        response_text
    )

    recommendations = {

        "interview":
            "INTERVIEW RESPONSE: Prepare for interview.",

        "rejected":
            "REJECTION RESPONSE: Close application.",

        "offer":
            "OFFER RESPONSE: Review offer with human.",

        "other":
            "OTHER RESPONSE: Human review required.",
    }

    return {

        "category": category,

        "recommendation":
            recommendations[category],

        "human_action_required": True,
    }


# ============================================================
# FULL RESPONSE ANALYSIS
# ============================================================

def analyze_response(response_text):
    """
    Analyze an employer response and produce
    a safe status recommendation.

    This function does NOT update application status.
    """

    details = explain_classification(
        response_text
    )

    category = details[
        "category"
    ]

    recommended_status = {

        "interview": "interview",

        "rejected": "rejected",

        "offer": "offer",

        "other": None,
    }[category]

    return {

        "category":
            category,

        "matched_keyword":
            details[
                "matched_keyword"
            ],

        "reason":
            details[
                "reason"
            ],

        "recommended_status":
            recommended_status,

        "human_action_required":
            True,
    }