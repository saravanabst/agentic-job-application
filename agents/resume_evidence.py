import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PROFILE_PATH = (
    BASE_DIR
    / "resumes"
    / "private"
    / "resume_profile.json"
)


def load_resume_profile():
    """Load the private candidate resume profile."""

    with open(
        PROFILE_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def collect_project_evidence(profile):
    """
    Build a mapping between skills and portfolio projects.

    Evidence is collected from both:
    - technologies
    - skills_demonstrated
    """

    evidence = {}

    projects = profile.get(
        "portfolio_projects",
        []
    )

    for project in projects:

        project_name = project.get(
            "name",
            ""
        )

        technologies = project.get(
            "technologies",
            []
        )

        skills_demonstrated = project.get(
            "skills_demonstrated",
            []
        )

        skills = (
            technologies
            + skills_demonstrated
        )

        for skill in skills:

            if skill not in evidence:

                evidence[skill] = []

            if project_name not in evidence[skill]:

                evidence[skill].append(
                    project_name
                )

    return evidence


def find_evidence(
    required_skills,
    preferred_skills,
    profile
):
    """Find genuine candidate evidence for job requirements."""

    evidence = collect_project_evidence(
        profile
    )

    required_matches = {}
    required_gaps = []

    preferred_matches = {}
    preferred_gaps = []

    # Required skills
    for skill in required_skills:

        if skill in evidence:

            required_matches[skill] = (
                evidence[skill]
            )

        else:

            required_gaps.append(skill)

    # Preferred skills
    for skill in preferred_skills:

        if skill in evidence:

            preferred_matches[skill] = (
                evidence[skill]
            )

        else:

            preferred_gaps.append(skill)

    return {
        "required_matches": required_matches,
        "required_gaps": required_gaps,
        "preferred_matches": preferred_matches,
        "preferred_gaps": preferred_gaps
    }


def print_evidence(result):

    print()
    print("RESUME EVIDENCE AGENT")
    print("=" * 60)

    print()
    print("REQUIRED SKILLS - EVIDENCE")

    if result["required_matches"]:

        for skill, projects in (
            result["required_matches"].items()
        ):

            print()
            print(f"{skill}:")

            for project in projects:

                print(
                    f"  -> {project}"
                )

    else:

        print("None")

    print()
    print("REQUIRED SKILLS - GAPS")

    if result["required_gaps"]:

        for skill in result["required_gaps"]:

            print(
                f"  GAP: {skill}"
            )

    else:

        print("None")

    print()
    print("PREFERRED SKILLS - EVIDENCE")

    if result["preferred_matches"]:

        for skill, projects in (
            result["preferred_matches"].items()
        ):

            print()
            print(f"{skill}:")

            for project in projects:

                print(
                    f"  -> {project}"
                )

    else:

        print("None")

    print()
    print("PREFERRED SKILLS - GAPS")

    if result["preferred_gaps"]:

        for skill in result["preferred_gaps"]:

            print(
                f"  GAP: {skill}"
            )

    else:

        print("None")


def main():

    profile = load_resume_profile()

    # Test job requirements
    required_skills = [
        "SQL",
        "Python",
        "Excel",
        "Tableau",
        "Data Cleaning",
        "Reporting"
    ]

    preferred_skills = [
        "Power BI",
        "Machine Learning",
        "Dashboarding"
    ]

    result = find_evidence(
        required_skills,
        preferred_skills,
        profile
    )

    print_evidence(result)


if __name__ == "__main__":
    main()