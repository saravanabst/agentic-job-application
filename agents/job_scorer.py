import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_json(file_path):
    """Load a JSON configuration file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_profile():
    """Load the private candidate profile."""
    profile_path = CONFIG_DIR / "job_profile.json"
    return load_json(profile_path)


def load_scoring_rules():
    """Load the scoring configuration."""
    rules_path = CONFIG_DIR / "scoring_rules.json"
    return load_json(rules_path)


def load_skill_aliases():
    """Load skill names and their known aliases."""
    aliases_path = CONFIG_DIR / "skill_aliases.json"
    return load_json(aliases_path)


def normalize_text(text):
    """Normalize text for matching."""
    return " ".join(text.lower().split())


def skill_found_in_job(skill, job_text, aliases):
    """
    Check whether a skill or any of its aliases
    appears in the job description.
    """
    normalized_job = normalize_text(job_text)

    possible_terms = [skill] + aliases.get(skill, [])

    for term in possible_terms:
        normalized_term = normalize_text(term)

        if normalized_term in normalized_job:
            return True

    return False


def find_skill_matches(job_text, profile, aliases):
    """
    Find candidate skills that are mentioned directly
    or indirectly through known aliases.
    """
    matched_skills = []
    missing_skills = []

    for skill_group in profile["technical_skills"].values():
        for skill in skill_group:

            if skill_found_in_job(skill, job_text, aliases):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

    return matched_skills, missing_skills


def calculate_technical_score(
    matched_skills,
    scoring_rules
):
    """Calculate the technical skills portion of the score."""

    high_priority = scoring_rules["skill_priority"]["high_priority"]
    medium_priority = scoring_rules["skill_priority"]["medium_priority"]
    bonus_skills = scoring_rules["skill_priority"]["bonus_skills"]

    high_matches = [
        skill for skill in matched_skills
        if skill in high_priority
    ]

    medium_matches = [
        skill for skill in matched_skills
        if skill in medium_priority
    ]

    bonus_matches = [
        skill for skill in matched_skills
        if skill in bonus_skills
    ]

    high_score = min(len(high_matches) * 2, 20)
    medium_score = min(len(medium_matches), 5)
    bonus_score = min(len(bonus_matches), 3)

    technical_score = min(
        high_score + medium_score + bonus_score,
        25
    )

    return {
        "technical_score": technical_score,
        "high_priority_matches": high_matches,
        "medium_priority_matches": medium_matches,
        "bonus_matches": bonus_matches
    }


def score_job(job_text):
    """
    Calculate the technical skill match for a job.

    This is version 2 of the scorer.
    It uses skill aliases to handle common terminology variations.
    """

    profile = load_profile()
    scoring_rules = load_scoring_rules()
    aliases = load_skill_aliases()

    matched_skills, missing_skills = find_skill_matches(
        job_text,
        profile,
        aliases
    )

    technical_result = calculate_technical_score(
        matched_skills,
        scoring_rules
    )

    return {
        "technical_score": technical_result["technical_score"],
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "high_priority_matches": technical_result[
            "high_priority_matches"
        ],
        "medium_priority_matches": technical_result[
            "medium_priority_matches"
        ],
        "bonus_matches": technical_result[
            "bonus_matches"
        ]
    }


if __name__ == "__main__":

    sample_job = """
    Data Analyst

    We are looking for a Data Analyst with strong SQL,
    Python, Pandas, Excel and Tableau skills.

    Experience with reporting, data cleaning and dashboards
    is highly desirable.
    """

    result = score_job(sample_job)

    print()
    print("JOB SCORING TEST - VERSION 2")
    print("=" * 45)

    print(
        f"Technical Score: "
        f"{result['technical_score']}/25"
    )

    print()
    print("Matched Skills:")

    for skill in result["matched_skills"]:
        print(f"  MATCH: {skill}")

    print()
    print("High Priority Matches:")

    for skill in result["high_priority_matches"]:
        print(f"  HIGH: {skill}")

    print()
    print("Medium Priority Matches:")

    for skill in result["medium_priority_matches"]:
        print(f"  MEDIUM: {skill}")

    print()
    print("Bonus Matches:")

    for skill in result["bonus_matches"]:
        print(f"  BONUS: {skill}")

    print()
    print("Skills Not Mentioned:")

    for skill in result["missing_skills"]:
        print(f"  NOT MENTIONED: {skill}")
