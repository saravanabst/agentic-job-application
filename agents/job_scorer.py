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


def normalize_text(text):
    """Convert text to lowercase for simple matching."""
    return text.lower().strip()


def find_skill_matches(job_text, profile):
    """Find skills from the candidate profile that appear in the job."""
    job_text = normalize_text(job_text)

    all_skills = []

    for skill_group in profile["technical_skills"].values():
        all_skills.extend(skill_group)

    matched_skills = []
    missing_skills = []

    for skill in all_skills:
        if normalize_text(skill) in job_text:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    return matched_skills, missing_skills


def score_job(job_text):
    """
    Calculate a first-pass technical skill match.

    This is intentionally simple. Later versions will use
    NLP/LLMs for deeper semantic matching.
    """
    profile = load_profile()
    rules = load_scoring_rules()

    matched_skills, missing_skills = find_skill_matches(
        job_text,
        profile
    )

    high_priority = rules["skill_priority"]["high_priority"]
    medium_priority = rules["skill_priority"]["medium_priority"]
    bonus_skills = rules["skill_priority"]["bonus_skills"]

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
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "high_priority_matches": high_matches,
        "medium_priority_matches": medium_matches,
        "bonus_matches": bonus_matches
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
    print("JOB SCORING TEST")
    print("=" * 40)
    print(f"Technical Score: {result['technical_score']}/25")

    print()
    print("Matched Skills:")
    for skill in result["matched_skills"]:
        print(f"  MATCH: {skill}")

    print()
    print("Missing Skills:")
    for skill in result["missing_skills"]:
        print(f"  MISSING: {skill}")
