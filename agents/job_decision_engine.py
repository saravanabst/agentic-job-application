import json
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

sys.path.insert(0, str(BASE_DIR / "agents"))

from candidate_matcher import analyze_candidate_against_job


def load_json(file_path):
    """Load a JSON configuration file."""

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_profile():
    """Load the private candidate profile."""

    return load_json(
        CONFIG_DIR / "job_profile.json"
    )


def load_scoring_rules():
    """Load scoring rules."""

    return load_json(
        CONFIG_DIR / "scoring_rules.json"
    )


def calculate_role_score(job_title, profile):
    """
    Calculate role relevance.

    Exact target role = full score.
    Secondary role = strong score.
    Related role = partial score.
    """

    weights = load_scoring_rules()["weights"]
    maximum = weights["role_relevance"]

    job_title_lower = job_title.lower()

    target_role = profile["candidate"]["target_role"].lower()

    secondary_roles = [
        role.lower()
        for role in profile["candidate"]["secondary_roles"]
    ]

    if target_role in job_title_lower:
        return maximum

    for role in secondary_roles:
        if role in job_title_lower:
            return round(maximum * 0.9)

    related_terms = [
        "data",
        "analytics",
        "business intelligence",
        "reporting",
        "insights",
        "operations"
    ]

    if any(
        term in job_title_lower
        for term in related_terms
    ):
        return round(maximum * 0.65)

    return 0


def calculate_technical_score(match_result):
    """Calculate technical skill score."""

    maximum = 25

    matched = len(
        match_result["required"]["matched"]
    )

    gaps = len(
        match_result["required"]["gaps"]
    )

    total = matched + gaps

    if total == 0:
        return maximum

    score = (
        matched / total
    ) * maximum

    return round(score)


def calculate_experience_score(job_text):
    """
    First version of experience scoring.

    We deliberately do not reject a candidate merely because
    a job asks for more experience.
    """

    maximum = 15

    text = job_text.lower()

    experience_indicators = [
        "years of experience",
        "years experience",
        "experience required",
        "experience in"
    ]

    if not any(
        indicator in text
        for indicator in experience_indicators
    ):
        return maximum

    # Conservative default:
    # experience requirements require review rather than
    # automatic rejection.
    return round(maximum * 0.75)


def calculate_location_score(
    job_location,
    work_mode,
    profile
):
    """Calculate location and work-mode compatibility."""

    maximum = 10

    preferred_locations = [
        location.lower()
        for location in profile["candidate"]["preferred_locations"]
    ]

    location_lower = job_location.lower()
    work_mode_lower = work_mode.lower()

    location_match = any(
        location in location_lower
        or location_lower in location
        for location in preferred_locations
    )

    preferred_modes = [
        mode.lower()
        for mode in profile["job_preferences"]["preferred_work_modes"]
    ]

    mode_match = any(
        mode in work_mode_lower
        for mode in preferred_modes
    )

    if location_match and mode_match:
        return maximum

    if location_match or mode_match:
        return 8

    return 5


def calculate_education_score(job_text, profile):
    """Calculate education relevance."""

    maximum = 10

    text = job_text.lower()

    education_terms = []

    for education in profile["education"]:

        qualification = education.get(
            "qualification",
            ""
        )

        specialization = education.get(
            "specialization",
            ""
        )

        education_terms.append(
            qualification.lower()
        )

        education_terms.append(
            specialization.lower()
        )

    relevant_terms = [
        "computer science",
        "data analytics",
        "business intelligence",
        "artificial intelligence",
        "machine learning",
        "statistics",
        "data science"
    ]

    matches = 0

    for term in relevant_terms:

        if term in text:

            if any(
                education_term in term
                or term in education_term
                for education_term in education_terms
            ):
                matches += 1

    if matches > 0:
        return maximum

    return round(maximum * 0.7)


def calculate_portfolio_score(match_result):
    """Calculate portfolio evidence score."""

    maximum = 10

    evidence_count = len(
        match_result["portfolio_evidence"]
    )

    if evidence_count >= 6:
        return 10

    if evidence_count >= 4:
        return 8

    if evidence_count >= 2:
        return 6

    if evidence_count >= 1:
        return 4

    return 0


def calculate_industry_score(job_text):
    """
    Initial industry-fit score.

    This is deliberately conservative.
    """

    maximum = 5

    text = job_text.lower()

    relevant_terms = [
        "analytics",
        "data",
        "business intelligence",
        "reporting",
        "operations"
    ]

    matches = sum(
        1
        for term in relevant_terms
        if term in text
    )

    if matches >= 3:
        return 5

    if matches >= 1:
        return 3

    return 2


def check_disqualifiers(
    job_text,
    job_location,
    profile
):
    """
    Check conditions that may prevent application.

    We do NOT automatically reject based on experience.
    """

    text = job_text.lower()

    reasons = []

    # Work-rights checks will become more sophisticated later.
    citizenship_required_terms = [
        "must be a new zealand citizen",
        "nz citizenship required",
        "citizens only",
        "new zealand citizens only"
    ]

    if any(
        term in text
        for term in citizenship_required_terms
    ):

        work_rights = profile[
            "candidate"
        ]["work_rights"].lower()

        if "permanent resident" in work_rights:

            reasons.append(
                "Job may require NZ citizenship."
            )

    return reasons


def make_decision(
    score,
    disqualifiers,
    profile
):
    """Convert score into an application decision."""

    if disqualifiers:
        return "REVIEW"

    preferences = profile["job_preferences"]

    priority_threshold = preferences[
        "priority_match_score"
    ]

    minimum_threshold = preferences[
        "minimum_match_score"
    ]

    if score >= priority_threshold:
        return "PRIORITY APPLY"

    if score >= minimum_threshold:
        return "APPLY"

    if score >= 65:
        return "REVIEW"

    return "IGNORE"


def analyze_job(
    job_title,
    job_location,
    work_mode,
    job_text
):
    """Run the complete decision engine."""

    profile = load_profile()

    match_analysis = (
        analyze_candidate_against_job(
            job_text
        )
    )

    match_result = match_analysis["match"]

    role_score = calculate_role_score(
        job_title,
        profile
    )

    technical_score = calculate_technical_score(
        match_result
    )

    experience_score = calculate_experience_score(
        job_text
    )

    location_score = calculate_location_score(
        job_location,
        work_mode,
        profile
    )

    education_score = calculate_education_score(
        job_text,
        profile
    )

    portfolio_score = calculate_portfolio_score(
        match_result
    )

    industry_score = calculate_industry_score(
        job_text
    )

    total_score = (
        role_score
        + technical_score
        + experience_score
        + location_score
        + education_score
        + portfolio_score
        + industry_score
    )

    disqualifiers = check_disqualifiers(
        job_text,
        job_location,
        profile
    )

    decision = make_decision(
        total_score,
        disqualifiers,
        profile
    )

    return {
        "job_title": job_title,
        "job_location": job_location,
        "work_mode": work_mode,
        "score": total_score,
        "decision": decision,
        "score_breakdown": {
            "role_relevance": role_score,
            "technical_skills": technical_score,
            "experience": experience_score,
            "location_and_work_mode": location_score,
            "education": education_score,
            "portfolio_evidence": portfolio_score,
            "industry_fit": industry_score
        },
        "required_matches": match_result[
            "required"
        ]["matched"],
        "required_gaps": match_result[
            "required"
        ]["gaps"],
        "preferred_matches": match_result[
            "preferred"
        ]["matched"],
        "preferred_gaps": match_result[
            "preferred"
        ]["gaps"],
        "portfolio_evidence": match_result[
            "portfolio_evidence"
        ],
        "risks": disqualifiers
    }


if __name__ == "__main__":

    sample_job_title = "Data Analyst"

    sample_location = "Auckland, New Zealand"

    sample_work_mode = "Hybrid"

    sample_job = """
    Data Analyst - Auckland

    Required skills:
    SQL, Python, Excel and Tableau.

    Candidates must have experience with
    data cleaning and reporting.

    Preferred skills:
    Power BI, Machine Learning and Azure.

    Experience with dashboards is desirable.

    This position requires 2 years of
    data analytics experience.
    """

    result = analyze_job(
        sample_job_title,
        sample_location,
        sample_work_mode,
        sample_job
    )

    print()
    print("JOB DECISION ENGINE")
    print("=" * 60)

    print()
    print(f"Job: {result['job_title']}")
    print(f"Location: {result['job_location']}")
    print(f"Work Mode: {result['work_mode']}")

    print()
    print(
        f"OVERALL SCORE: "
        f"{result['score']}/100"
    )

    print(
        f"DECISION: "
        f"{result['decision']}"
    )

    print()
    print("SCORE BREAKDOWN")
    print("-" * 60)

    for factor, score in result[
        "score_breakdown"
    ].items():

        print(
            f"{factor}: {score}"
        )

    print()
    print("REQUIRED SKILLS - MATCHED")

    for skill in result["required_matches"]:
        print(f"  MATCH: {skill}")

    print()
    print("REQUIRED SKILLS - GAPS")

    for skill in result["required_gaps"]:
        print(f"  GAP: {skill}")

    print()
    print("PREFERRED SKILLS - MATCHED")

    for skill in result["preferred_matches"]:
        print(f"  MATCH: {skill}")

    print()
    print("PREFERRED SKILLS - GAPS")

    for skill in result["preferred_gaps"]:
        print(f"  GAP: {skill}")

    print()
    print("PORTFOLIO EVIDENCE")

    for skill, projects in result[
        "portfolio_evidence"
    ].items():

        print(f"  {skill}:")

        for project in projects:
            print(f"      -> {project}")

    print()

    if result["risks"]:

        print("RISKS")

        for risk in result["risks"]:
            print(f"  WARNING: {risk}")

    else:

        print("RISKS")
        print("  None detected.")
