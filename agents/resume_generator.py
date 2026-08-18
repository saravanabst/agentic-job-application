import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PRIVATE_RESUME = (
    BASE_DIR
    / "resumes"
    / "private"
    / "resume_profile.json"
)

TAILORING_DIR = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
)

OUTPUT_DIR = (
    BASE_DIR
    / "resumes"
    / "private"
    / "generated"
)


def load_json(file_path):
    """Load JSON safely."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def normalize(text):
    """Normalize text for comparisons."""

    return str(text).strip().lower()


def get_project_by_name(
    resume,
    project_name
):
    """Return a portfolio project by name."""

    projects = resume.get(
        "portfolio_projects",
        []
    )

    for project in projects:

        if normalize(
            project.get("name", "")
        ) == normalize(project_name):

            return project

    return None


def build_professional_summary(
    resume,
    tailoring_plan
):
    """
    Build a conservative professional summary.

    Only uses information already present
    in the candidate resume profile.
    """

    professional_summary = resume.get(
        "professional_summary",
        {}
    )

    target_role = professional_summary.get(
        "target_role",
        "Data Analyst"
    )

    original_summary = professional_summary.get(
        "summary",
        ""
    ).strip()

    matched_required = tailoring_plan.get(
        "matched_required_skills",
        []
    )

    matched_preferred = tailoring_plan.get(
        "matched_preferred_skills",
        []
    )

    priority_skills = (
        matched_required
        + matched_preferred
    )

    if original_summary:

        summary = original_summary

    else:

        skill_text = ", ".join(
            priority_skills
        )

        if skill_text:

            summary = (
                f"{target_role} candidate with "
                f"hands-on experience in "
                f"{skill_text}. "
                f"Experienced in applying "
                f"data analytics and technical "
                f"skills through practical "
                f"portfolio projects."
            )

        else:

            summary = (
                f"{target_role} candidate with "
                f"practical data analytics "
                f"project experience."
            )

    return summary


def build_skills_section(
    resume,
    tailoring_plan
):
    """
    Build a prioritized technical skills section.

    Matched job skills are placed first,
    followed by remaining verified skills.
    """

    technical_skills = resume.get(
        "technical_skills",
        {}
    )

    matched_skills = (
        tailoring_plan.get(
            "matched_required_skills",
            []
        )
        +
        tailoring_plan.get(
            "matched_preferred_skills",
            []
        )
    )

    matched_lookup = {
        normalize(skill)
        for skill in matched_skills
    }

    prioritized = []
    remaining = []

    for skill_group in technical_skills.values():

        for skill in skill_group:

            if normalize(skill) in matched_lookup:

                if skill not in prioritized:
                    prioritized.append(skill)

            else:

                if skill not in remaining:
                    remaining.append(skill)

    return {
        "priority_skills": prioritized,
        "additional_skills": remaining
    }


def build_project_section(
    resume,
    tailoring_plan
):
    """
    Build project descriptions using only
    verified portfolio evidence.
    """

    selected_projects = tailoring_plan.get(
        "recommended_projects",
        []
    )

    generated_projects = []

    for selected in selected_projects:

        project_name = selected.get(
            "project",
            ""
        )

        project = get_project_by_name(
            resume,
            project_name
        )

        if not project:
            continue

        generated_projects.append(
            {
                "name": project.get(
                    "name",
                    ""
                ),

                "category": project.get(
                    "category",
                    ""
                ),

                "technologies": project.get(
                    "technologies",
                    []
                ),

                "skills_demonstrated": project.get(
                    "skills_demonstrated",
                    []
                ),

                "achievements": project.get(
                    "achievements",
                    []
                ),

                "relevance_score": selected.get(
                    "relevance_score",
                    0
                ),

                "matching_skills": selected.get(
                    "matching_skills",
                    []
                )
            }
        )

    return generated_projects


def build_education_section(resume):
    """Return verified education only."""

    education = resume.get(
        "education",
        []
    )

    result = []

    for item in education:

        result.append(
            item
        )

    return result


def build_experience_section(resume):
    """
    Return verified employment experience only.

    Empty experience records are excluded.
    """

    experience = resume.get(
        "experience",
        []
    )

    result = []

    for item in experience:

        company = item.get(
            "company",
            ""
        ).strip()

        title = item.get(
            "job_title",
            ""
        ).strip()

        if not company and not title:
            continue

        result.append(
            item
        )

    return result


def build_resume(
    resume,
    tailoring_plan
):
    """Build the complete tailored resume structure."""

    safety = tailoring_plan.get(
        "safety",
        {}
    )

    resume_data = {
        "generation_version": "1.0",

        "job_target": {
            "job_id": tailoring_plan.get(
                "job",
                {}
            ).get(
                "job_id",
                ""
            ),

            "company": tailoring_plan.get(
                "job",
                {}
            ).get(
                "company",
                ""
            ),

            "title": tailoring_plan.get(
                "job",
                {}
            ).get(
                "title",
                ""
            ),

            "location": tailoring_plan.get(
                "job",
                {}
            ).get(
                "location",
                ""
            ),

            "work_mode": tailoring_plan.get(
                "job",
                {}
            ).get(
                "work_mode",
                ""
            )
        },

        "candidate": {
            "full_name": resume.get(
                "personal",
                {}
            ).get(
                "full_name",
                ""
            ),

            "email": resume.get(
                "personal",
                {}
            ).get(
                "email",
                ""
            ),

            "phone": resume.get(
                "personal",
                {}
            ).get(
                "phone",
                ""
            ),

            "linkedin_url": resume.get(
                "personal",
                {}
            ).get(
                "linkedin_url",
                ""
            ),

            "github_url": resume.get(
                "personal",
                {}
            ).get(
                "github_url",
                ""
            ),

            "location": resume.get(
                "personal",
                {}
            ).get(
                "location",
                ""
            ),

            "work_rights": resume.get(
                "personal",
                {}
            ).get(
                "work_rights",
                ""
            )
        },

        "professional_summary": build_professional_summary(
            resume,
            tailoring_plan
        ),

        "technical_skills": build_skills_section(
            resume,
            tailoring_plan
        ),

        "experience": build_experience_section(
            resume
        ),

        "education": build_education_section(
            resume
        ),

        "portfolio_projects": build_project_section(
            resume,
            tailoring_plan
        ),

        "certifications": resume.get(
            "certifications",
            []
        ),

        "additional_information": resume.get(
            "additional_information",
            {}
        ),

        "safety": {
            "invented_experience": safety.get(
                "invented_experience",
                False
            ),

            "invented_skills": safety.get(
                "invented_skills",
                False
            ),

            "invented_education": safety.get(
                "invented_education",
                False
            ),

            "invented_employment": safety.get(
                "invented_employment",
                False
            ),

            "personal_data_exposed": safety.get(
                "personal_data_exposed",
                False
            ),

            "automatic_submission": False,

            "human_review_required": True
        }
    }

    return resume_data


def save_resume(
    resume_data
):
    """Save generated tailored resume privately."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    job_id = resume_data[
        "job_target"
    ].get(
        "job_id",
        "unknown"
    )

    output_file = (
        OUTPUT_DIR
        / f"{job_id}_tailored_resume.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            resume_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_file


def print_resume(
    resume_data
):
    """Display generated resume summary."""

    print()
    print("TAILORED RESUME GENERATOR")
    print("=" * 60)

    job = resume_data[
        "job_target"
    ]

    print()
    print(
        f"Target Job: "
        f"{job.get('title', '')}"
    )

    print(
        f"Company: "
        f"{job.get('company', '')}"
    )

    print(
        f"Location: "
        f"{job.get('location', '')}"
    )

    print()
    print("PROFESSIONAL SUMMARY")

    print(
        resume_data[
            "professional_summary"
        ]
    )

    print()
    print("PRIORITY SKILLS")

    priority_skills = (
        resume_data[
            "technical_skills"
        ].get(
            "priority_skills",
            []
        )
    )

    if priority_skills:

        for skill in priority_skills:
            print(
                f"  - {skill}"
            )

    else:

        print("  None")

    print()
    print("ADDITIONAL VERIFIED SKILLS")

    additional_skills = (
        resume_data[
            "technical_skills"
        ].get(
            "additional_skills",
            []
        )
    )

    if additional_skills:

        for skill in additional_skills:
            print(
                f"  - {skill}"
            )

    else:

        print("  None")

    print()
    print("PORTFOLIO PROJECTS")

    projects = resume_data.get(
        "portfolio_projects",
        []
    )

    if not projects:

        print("  None")

    for project in projects:

        print()
        print(
            f"  {project['name']}"
        )

        print(
            f"      Relevance: "
            f"{project['relevance_score']}"
        )

        print(
            "      Matching skills: "
            +
            (
                ", ".join(
                    project[
                        "matching_skills"
                    ]
                )
                if project[
                    "matching_skills"
                ]
                else "None"
            )
        )

        print(
            "      Technologies: "
            +
            ", ".join(
                project[
                    "technologies"
                ]
            )
        )

    print()
    print("EDUCATION")

    education = resume_data.get(
        "education",
        []
    )

    for item in education:

        qualification = item.get(
            "qualification",
            ""
        )

        specialization = item.get(
            "specialization",
            ""
        )

        level = item.get(
            "level",
            ""
        )

        text = qualification

        if specialization:
            text += (
                f" - {specialization}"
            )

        if level:
            text += (
                f" - {level}"
            )

        print(
            f"  - {text}"
        )

    print()
    print("SAFETY CHECK")

    safety = resume_data[
        "safety"
    ]

    print(
        f"  Invented experience: "
        f"{safety['invented_experience']}"
    )

    print(
        f"  Invented skills: "
        f"{safety['invented_skills']}"
    )

    print(
        f"  Invented education: "
        f"{safety['invented_education']}"
    )

    print(
        f"  Invented employment: "
        f"{safety['invented_employment']}"
    )

    print(
        f"  Personal data exposed: "
        f"{safety['personal_data_exposed']}"
    )

    print(
        f"  Automatic submission: "
        f"{safety['automatic_submission']}"
    )

    print(
        f"  Human review required: "
        f"{safety['human_review_required']}"
    )


def main():

    print()
    print("RESUME GENERATOR TEST")
    print("=" * 60)

    if not PRIVATE_RESUME.exists():

        print()
        print(
            "ERROR: Resume profile not found:"
        )

        print(
            PRIVATE_RESUME
        )

        return

    tailoring_files = sorted(
        TAILORING_DIR.glob(
            "*_tailoring_plan.json"
        )
    )

    if not tailoring_files:

        print()
        print(
            "ERROR: No tailoring plan found."
        )

        print(
            "Run resume_tailor.py first."
        )

        return

    tailoring_file = (
        tailoring_files[-1]
    )

    print()
    print(
        f"Using tailoring plan:"
    )

    print(
        tailoring_file
    )

    resume = load_json(
        PRIVATE_RESUME
    )

    tailoring_plan = load_json(
        tailoring_file
    )

    resume_data = build_resume(
        resume,
        tailoring_plan
    )

    print_resume(
        resume_data
    )

    output_file = save_resume(
        resume_data
    )

    print()
    print(
        "Tailored resume saved privately:"
    )

    print(
        output_file
    )


if __name__ == "__main__":
    main()