import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_json(file_path):
    """Load a JSON configuration file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_skill_aliases():
    """Load skill aliases."""
    return load_json(CONFIG_DIR / "skill_aliases.json")


def normalize_text(text):
    """Normalize text for matching."""
    return " ".join(text.lower().split())


def extract_skills(job_text):
    """Identify known skills mentioned in a job description."""

    normalized_job = normalize_text(job_text)
    aliases = load_skill_aliases()

    found_skills = []

    for skill, skill_aliases in aliases.items():

        possible_terms = [skill] + skill_aliases

        for term in possible_terms:

            if normalize_text(term) in normalized_job:
                found_skills.append(skill)
                break

    return sorted(set(found_skills))


def split_requirement_sections(job_text):
    """
    Split a job description into required, preferred and general sections.

    This is a deterministic first version.
    """

    lines = job_text.splitlines()

    sections = {
        "required": [],
        "preferred": [],
        "general": []
    }

    current_section = "general"

    required_headers = [
        "required",
        "required skills",
        "requirements",
        "essential skills",
        "must have",
        "essential requirements"
    ]

    preferred_headers = [
        "preferred",
        "preferred skills",
        "nice to have",
        "nice-to-have",
        "desirable",
        "bonus skills"
    ]

    for line in lines:

        clean_line = line.strip()
        normalized_line = clean_line.lower().rstrip(":")

        if not clean_line:
            continue

        if any(
            normalized_line == header
            for header in required_headers
        ):
            current_section = "required"
            continue

        if any(
            normalized_line == header
            for header in preferred_headers
        ):
            current_section = "preferred"
            continue

        sections[current_section].append(clean_line)

    return {
        key: " ".join(value)
        for key, value in sections.items()
    }


def find_skills_in_text(text, aliases):
    """Find known skills in a specific section."""

    normalized_text = normalize_text(text)

    found = []

    for skill, skill_aliases in aliases.items():

        possible_terms = [skill] + skill_aliases

        for term in possible_terms:

            if normalize_text(term) in normalized_text:
                found.append(skill)
                break

    return sorted(set(found))


def classify_requirements(job_text):
    """
    Extract required and preferred skills based on
    explicit job-description sections.
    """

    aliases = load_skill_aliases()

    sections = split_requirement_sections(job_text)

    required = find_skills_in_text(
        sections["required"],
        aliases
    )

    preferred = find_skills_in_text(
        sections["preferred"],
        aliases
    )

    general = find_skills_in_text(
        sections["general"],
        aliases
    )

    # If a skill is explicitly required or preferred,
    # remove it from the general category.
    general = [
        skill for skill in general
        if skill not in required
        and skill not in preferred
    ]

    return {
        "required": required,
        "preferred": preferred,
        "unspecified": general
    }


def analyze_job(job_text):
    """Complete job requirement analysis."""

    detected_skills = extract_skills(job_text)

    requirements = classify_requirements(job_text)

    return {
        "detected_skills": detected_skills,
        "requirements": requirements
    }


if __name__ == "__main__":

    sample_job = """
    Data Analyst - Auckland

    Required skills:
    SQL, Python, Excel and Tableau.

    Candidates must have experience with
    data cleaning and reporting.

    Preferred skills:
    Power BI, Machine Learning and Azure.

    Experience with dashboards is desirable.
    """

    result = analyze_job(sample_job)

    print()
    print("JOB REQUIREMENT EXTRACTION TEST - VERSION 2")
    print("=" * 55)

    print()
    print("Detected Skills:")

    for skill in result["detected_skills"]:
        print(f"  DETECTED: {skill}")

    print()
    print("Required Skills:")

    for skill in result["requirements"]["required"]:
        print(f"  REQUIRED: {skill}")

    print()
    print("Preferred Skills:")

    for skill in result["requirements"]["preferred"]:
        print(f"  PREFERRED: {skill}")

    print()
    print("Unspecified Skills:")

    for skill in result["requirements"]["unspecified"]:
        print(f"  UNSPECIFIED: {skill}")
