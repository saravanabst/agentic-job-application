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

    return load_json(
        CONFIG_DIR / "job_profile.json"
    )


def load_requirements():
    """Import the job requirement extractor."""

    import sys

    sys.path.insert(
        0,
        str(BASE_DIR / "agents")
    )

    from job_requirements import analyze_job

    return analyze_job


def build_candidate_skill_set(profile):
    """Create a normalized candidate skill set."""

    skills = set()

    for skill_group in profile["technical_skills"].values():

        for skill in skill_group:
            skills.add(skill.lower())

    return skills


def build_portfolio_evidence(profile):
    """
    Map skills/capabilities to portfolio projects.
    """

    evidence = {}

    for project in profile["portfolio_projects"]:

        project_name = project["name"]

        items = (
            project.get("technologies", [])
            + project.get("capabilities", [])
        )

        for item in items:

            key = item.lower()

            if key not in evidence:
                evidence[key] = []

            evidence[key].append(project_name)

    return evidence


def find_candidate_match(
    skill,
    candidate_skills
):
    """Check whether candidate has a skill."""

    return skill.lower() in candidate_skills


def find_portfolio_evidence(
    skill,
    portfolio_evidence
):
    """
    Find portfolio projects supporting a skill.
    """

    skill_lower = skill.lower()

    matching_projects = []

    for evidence_skill, projects in portfolio_evidence.items():

        if (
            skill_lower == evidence_skill
            or skill_lower in evidence_skill
            or evidence_skill in skill_lower
        ):

            matching_projects.extend(projects)

    return sorted(set(matching_projects))


def match_requirements(
    requirements,
    candidate_skills,
    portfolio_evidence
):
    """Compare job requirements against candidate."""

    result = {
        "required": {
            "matched": [],
            "gaps": []
        },
        "preferred": {
            "matched": [],
            "gaps": []
        },
        "portfolio_evidence": {}
    }

    for skill in requirements["required"]:

        if find_candidate_match(
            skill,
            candidate_skills
        ):

            result["required"]["matched"].append(
                skill
            )

        else:

            result["required"]["gaps"].append(
                skill
            )

    for skill in requirements["preferred"]:

        if find_candidate_match(
            skill,
            candidate_skills
        ):

            result["preferred"]["matched"].append(
                skill
            )

        else:

            result["preferred"]["gaps"].append(
                skill
            )

    all_matched = (
        result["required"]["matched"]
        + result["preferred"]["matched"]
    )

    for skill in all_matched:

        evidence = find_portfolio_evidence(
            skill,
            portfolio_evidence
        )

        if evidence:
            result["portfolio_evidence"][skill] = evidence

    return result


def calculate_match_score(
    match_result
):
    """
    Calculate a simple 100-point match score.

    Required skills have more weight than preferred skills.
    """

    required_matched = len(
        match_result["required"]["matched"]
    )

    required_total = (
        required_matched
        + len(
            match_result["required"]["gaps"]
        )
    )

    preferred_matched = len(
        match_result["preferred"]["matched"]
    )

    preferred_total = (
        preferred_matched
        + len(
            match_result["preferred"]["gaps"]
        )
    )

    if required_total > 0:
        required_score = (
            required_matched
            / required_total
        ) * 70
    else:
        required_score = 70

    if preferred_total > 0:
        preferred_score = (
            preferred_matched
            / preferred_total
        ) * 20
    else:
        preferred_score = 20

    portfolio_count = len(
        match_result["portfolio_evidence"]
    )

    portfolio_score = min(
        portfolio_count,
        5
    )

    score = round(
        required_score
        + preferred_score
        + portfolio_score
    )

    return min(score, 100)


def get_recommendation(score):

    if score >= 85:
        return "PRIORITY APPLY"

    if score >= 75:
        return "APPLY"

    if score >= 65:
        return "REVIEW"

    if score >= 50:
        return "LOW PRIORITY"

    return "IGNORE"


def analyze_candidate_against_job(
    job_text
):
    """Complete candidate-job matching process."""

    profile = load_profile()

    analyze_job = load_requirements()

    job_analysis = analyze_job(
        job_text
    )

    candidate_skills = build_candidate_skill_set(
        profile
    )

    portfolio_evidence = build_portfolio_evidence(
        profile
    )

    match_result = match_requirements(
        job_analysis["requirements"],
        candidate_skills,
        portfolio_evidence
    )

    score = calculate_match_score(
        match_result
    )

    recommendation = get_recommendation(
        score
    )

    return {
        "job_analysis": job_analysis,
        "match": match_result,
        "score": score,
        "recommendation": recommendation
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

    result = analyze_candidate_against_job(
        sample_job
    )

    print()
    print("CANDIDATE VS JOB MATCH")
    print("=" * 55)

    print()
    print(
        f"MATCH SCORE: "
        f"{result['score']}/100"
    )

    print(
        f"RECOMMENDATION: "
        f"{result['recommendation']}"
    )

    print()
    print("REQUIRED SKILLS - MATCHED")

    for skill in result["match"]["required"]["matched"]:
        print(f"  MATCH: {skill}")

    print()
    print("REQUIRED SKILLS - GAPS")

    for skill in result["match"]["required"]["gaps"]:
        print(f"  GAP: {skill}")

    print()
    print("PREFERRED SKILLS - MATCHED")

    for skill in result["match"]["preferred"]["matched"]:
        print(f"  MATCH: {skill}")

    print()
    print("PREFERRED SKILLS - GAPS")

    for skill in result["match"]["preferred"]["gaps"]:
        print(f"  GAP: {skill}")

    print()
    print("PORTFOLIO EVIDENCE")

    for skill, projects in result[
        "match"
    ]["portfolio_evidence"].items():

        print(f"  {skill}:")

        for project in projects:
            print(f"      -> {project}")
