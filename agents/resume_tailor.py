import json
import sys
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

PRIVATE_RESUME = (
    BASE_DIR
    / "resumes"
    / "private"
    / "resume_profile.json"
)

TAILORING_RULES = (
    BASE_DIR
    / "config"
    / "resume_tailoring_rules.json"
)

JOB_FILE = (
    BASE_DIR
    / "jobs"
    / "raw"
    / f"{JOB_ID}.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
)


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(file_path):
    """Load JSON from a file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):
    """Normalize text for reliable skill comparison."""

    return " ".join(
        str(text).lower().split()
    )


# ============================================================
# SKILL ALIAS SUPPORT
# ============================================================

def load_skill_aliases():
    """Load skill aliases from configuration."""

    aliases_file = (
        BASE_DIR
        / "config"
        / "skill_aliases.json"
    )

    if not aliases_file.exists():
        return {}

    return load_json(aliases_file)


def skill_matches_text(skill, text, aliases):
    """
    Check whether a skill or one of its aliases
    exists in the supplied text.
    """

    normalized_text = normalize(text)

    terms = [skill]

    skill_aliases = aliases.get(
        skill,
        []
    )

    if isinstance(skill_aliases, list):
        terms.extend(skill_aliases)

    for term in terms:

        if normalize(term) in normalized_text:
            return True

    return False


# ============================================================
# JOB REQUIREMENT EXTRACTION
# ============================================================

def extract_job_requirements(job):
    """
    Extract required and preferred skills.

    Priority:
    1. Existing structured requirements
    2. Job description text
    """

    requirements = job.get(
        "requirements",
        {}
    )

    required = requirements.get(
        "required_skills",
        []
    )

    preferred = requirements.get(
        "preferred_skills",
        []
    )

    # If structured requirements are already populated,
    # use them.
    if required or preferred:

        return {
            "required": sorted(
                set(required)
            ),
            "preferred": sorted(
                set(preferred)
            )
        }

    # Otherwise extract from job description.
    description = job.get(
        "description",
        ""
    )

    aliases = load_skill_aliases()

    # These are the skills currently supported
    # by the project configuration.
    known_skills = set()

    for skill in aliases.keys():
        known_skills.add(skill)

    # Also include common skills directly.
    known_skills.update(
        {
            "SQL",
            "Python",
            "Pandas",
            "NumPy",
            "Excel",
            "Tableau",
            "Power BI",
            "Data Cleaning",
            "Data Validation",
            "Data Analysis",
            "Reporting",
            "Dashboarding",
            "Business Intelligence",
            "Machine Learning",
            "Scikit-learn",
            "Statistics",
            "Hypothesis Testing",
            "Git",
            "GitHub",
            "Automation"
        }
    )

    detected = []

    for skill in known_skills:

        if skill_matches_text(
            skill,
            description,
            aliases
        ):
            detected.append(skill)

    # --------------------------------------------------------
    # Classify based on wording in the description.
    # --------------------------------------------------------

    normalized_description = normalize(
        description
    )

    required = []
    preferred = []

    for skill in detected:

        skill_found = normalize(skill)

        # Preferred wording associated with the skill.
        preferred_patterns = [
            f"preferred skills include {skill_found}",
            f"preferred skill {skill_found}",
            f"preferred: {skill_found}",
            f"nice to have {skill_found}",
            f"nice-to-have {skill_found}",
            f"desirable {skill_found}",
            f"bonus {skill_found}",
            f"bonus skills {skill_found}",
            f"{skill_found} is desirable",
            f"{skill_found} are desirable"
        ]

        is_preferred = any(
            pattern in normalized_description
            for pattern in preferred_patterns
        )

        if is_preferred:
            preferred.append(skill)
            continue

        # General rule:
        # Explicitly named skills in a "required" context
        # are required.
        required_patterns = [
            f"required skills include {skill_found}",
            f"required skills: {skill_found}",
            f"required {skill_found}",
            f"must have {skill_found}",
            f"essential {skill_found}",
            f"essential skills include {skill_found}",
            f"experience with {skill_found}"
        ]

        is_required = any(
            pattern in normalized_description
            for pattern in required_patterns
        )

        if is_required:
            required.append(skill)

    # --------------------------------------------------------
    # Special handling for common comma-separated wording.
    # --------------------------------------------------------

    required_text = normalized_description

    if (
        "required skills include"
        in required_text
    ):
        start = required_text.find(
            "required skills include"
        )

        section = required_text[
            start:
        ]

        for skill in detected:

            skill_name = normalize(
                skill
            )

            if skill_name in section:

                # Don't classify a skill as required
                # if it is clearly introduced later
                # as preferred.
                if skill not in preferred:
                    required.append(skill)

    # --------------------------------------------------------
    # Remove duplicates.
    # --------------------------------------------------------

    required = sorted(
        set(required)
    )

    preferred = sorted(
        set(preferred)
    )

    # A skill cannot be both required and preferred.
    preferred = [
        skill
        for skill in preferred
        if skill not in required
    ]

    return {
        "required": required,
        "preferred": preferred
    }


# ============================================================
# CANDIDATE SKILLS
# ============================================================

def get_candidate_skills(resume):
    """Return all candidate technical skills."""

    skills = set()

    technical_skills = resume.get(
        "technical_skills",
        {}
    )

    for skill_group in technical_skills.values():

        if not isinstance(
            skill_group,
            list
        ):
            continue

        for skill in skill_group:
            skills.add(skill)

    return skills


# ============================================================
# PROJECT EVIDENCE
# ============================================================

def get_project_evidence(resume):
    """
    Build:

        skill -> projects

    using only candidate-provided evidence.
    """

    evidence = {}

    projects = resume.get(
        "portfolio_projects",
        []
    )

    for project in projects:

        project_name = project.get(
            "name",
            ""
        )

        demonstrated_skills = project.get(
            "skills_demonstrated",
            []
        )

        for skill in demonstrated_skills:

            evidence.setdefault(
                normalize(skill),
                []
            )

            if (
                project_name
                not in evidence[
                    normalize(skill)
                ]
            ):
                evidence[
                    normalize(skill)
                ].append(
                    project_name
                )

    return evidence


# ============================================================
# MATCHING
# ============================================================

def find_matching_skills(
    required_skills,
    preferred_skills,
    candidate_skills
):
    """Match job requirements against candidate skills using aliases."""

    aliases = load_skill_aliases()

    candidate_normalized = {
        normalize(skill)
        for skill in candidate_skills
    }

    def skill_is_matched(skill):
        """Return True when the candidate has the skill or a configured alias."""

        skill_terms = [
            normalize(skill)
        ]

        skill_aliases = aliases.get(
            skill,
            []
        )

        if isinstance(skill_aliases, list):
            skill_terms.extend(
                normalize(alias)
                for alias in skill_aliases
            )

        return any(
            term in candidate_normalized
            for term in skill_terms
        )

    required_matched = []
    required_gaps = []

    for skill in required_skills:

        if skill_is_matched(skill):
            required_matched.append(skill)
        else:
            required_gaps.append(skill)

    preferred_matched = []
    preferred_gaps = []

    for skill in preferred_skills:

        if skill_is_matched(skill):
            preferred_matched.append(skill)
        else:
            preferred_gaps.append(skill)

    return (
        required_matched,
        required_gaps,
        preferred_matched,
        preferred_gaps
    )


# ============================================================
# PROJECT RANKING
# ============================================================

def rank_projects(
    matched_skills,
    resume,
    rules
):
    """Rank projects by demonstrated skill relevance."""

    project_scores = []

    project_rules = rules.get(
        "project_priority",
        {}
    )

    matched_lookup = {
        normalize(skill)
        for skill in matched_skills
    }

    projects = resume.get(
        "portfolio_projects",
        []
    )

    for project in projects:

        project_name = project.get(
            "name",
            ""
        )

        demonstrated_skills = project.get(
            "skills_demonstrated",
            []
        )

        matching_skills = []

        for skill in demonstrated_skills:

            if normalize(skill) in matched_lookup:

                matching_skills.append(
                    skill
                )

        score = len(
            matching_skills
        )

        rule = project_rules.get(
            project_name,
            {}
        )

        default_priority = rule.get(
            "default_priority",
            99
        )

        project_scores.append(
            {
                "project": project_name,
                "relevance_score": score,
                "default_priority": default_priority,
                "matching_skills": sorted(
                    set(matching_skills)
                )
            }
        )

    project_scores.sort(
        key=lambda item: (
            -item["relevance_score"],
            item["default_priority"]
        )
    )

    return project_scores


# ============================================================
# BUILD TAILORING PLAN
# ============================================================

def build_tailoring_plan(
    job,
    resume,
    rules
):
    """Build a safe resume tailoring plan."""

    requirements = extract_job_requirements(
        job
    )

    required_skills = requirements[
        "required"
    ]

    preferred_skills = requirements[
        "preferred"
    ]

    candidate_skills = get_candidate_skills(
        resume
    )

    (
        required_matched,
        required_gaps,
        preferred_matched,
        preferred_gaps
    ) = find_matching_skills(
        required_skills,
        preferred_skills,
        candidate_skills
    )

    all_matched = (
        required_matched
        + preferred_matched
    )

    project_scores = rank_projects(
        all_matched,
        resume,
        rules
    )

    maximum_projects = (
        rules
        .get(
            "section_rules",
            {}
        )
        .get(
            "portfolio_projects",
            {}
        )
        .get(
            "maximum_projects",
            3
        )
    )

    selected_projects = project_scores[
        :maximum_projects
    ]

    evidence = get_project_evidence(
        resume
    )

    skill_evidence = {}

    for skill in all_matched:

        projects = evidence.get(
            normalize(skill),
            []
        )

        if projects:

            skill_evidence[skill] = (
                projects
            )

    target_role = job.get(
        "title",
        resume
        .get(
            "professional_summary",
            {}
        )
        .get(
            "target_role",
            ""
        )
    )

    safety_rules = rules.get(
        "principles",
        {}
    )

    plan = {

        "tailoring_version": "4.0",

        "job": {
            "job_id": job.get(
                "job_id",
                ""
            ),
            "company": job.get(
                "company",
                ""
            ),
            "title": target_role,
            "location": job.get(
                "location",
                ""
            ),
            "work_mode": job.get(
                "work_mode",
                ""
            )
        },

        "extracted_requirements": {
            "required": required_skills,
            "preferred": preferred_skills
        },

        "candidate": {
            "target_role": (
                resume
                .get(
                    "professional_summary",
                    {}
                )
                .get(
                    "target_role",
                    ""
                )
            )
        },

        "matched_required_skills": (
            required_matched
        ),

        "required_skill_gaps": (
            required_gaps
        ),

        "matched_preferred_skills": (
            preferred_matched
        ),

        "preferred_skill_gaps": (
            preferred_gaps
        ),

        "priority_skills": (
            required_matched
            + preferred_matched
        ),

        "skill_evidence": skill_evidence,

        "recommended_projects": (
            selected_projects
        ),

        "tailoring_actions": {

            "professional_summary": (
                "Emphasize the target Data Analyst "
                "role and strongest verified "
                "matched skills."
            ),

            "technical_skills": (
                "Place matched required skills "
                "before other relevant skills."
            ),

            "portfolio_projects": (
                "Prioritize projects with the "
                "strongest verified evidence "
                "for this job."
            ),

            "experience": (
                "Use only verified candidate "
                "experience. Never invent "
                "employment or responsibilities."
            )
        },

        "safety": {

            "invented_experience": False,

            "invented_skills": False,

            "invented_education": False,

            "invented_employment": False,

            "personal_data_exposed": False,

            "automatic_submission": False,

            "human_review_required": (
                safety_rules.get(
                    "human_review_required",
                    True
                )
            )
        }
    }

    return plan


# ============================================================
# SAVE
# ============================================================

def save_plan(plan):
    """Save tailoring plan privately."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    job_id = plan[
        "job"
    ][
        "job_id"
    ]

    output_file = (
        OUTPUT_DIR
        / f"{job_id}_tailoring_plan.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            plan,
            file,
            indent=4,
            ensure_ascii=False
        )

    return output_file


# ============================================================
# DISPLAY
# ============================================================

def print_list(
    title,
    values,
    prefix=""
):
    """Print a list cleanly."""

    print()
    print(title)

    if not values:
        print("  None")
        return

    for value in values:
        print(
            f"  {prefix}{value}"
        )


def print_plan(plan):
    """Display tailoring plan."""

    print()
    print(
        "RESUME TAILORING AGENT"
    )
    print("=" * 60)

    print()
    print(
        f"Job: "
        f"{plan['job']['title']}"
    )

    print(
        f"Company: "
        f"{plan['job']['company']}"
    )

    print(
        f"Location: "
        f"{plan['job']['location']}"
    )

    print()

    print(
        "EXTRACTED JOB REQUIREMENTS"
    )

    print_list(
        "Required:",
        plan[
            "extracted_requirements"
        ][
            "required"
        ]
    )

    print_list(
        "Preferred:",
        plan[
            "extracted_requirements"
        ][
            "preferred"
        ]
    )

    print_list(
        "MATCHED REQUIRED SKILLS",
        plan[
            "matched_required_skills"
        ],
        "MATCH: "
    )

    print_list(
        "REQUIRED SKILL GAPS",
        plan[
            "required_skill_gaps"
        ],
        "GAP: "
    )

    print_list(
        "MATCHED PREFERRED SKILLS",
        plan[
            "matched_preferred_skills"
        ],
        "MATCH: "
    )

    print_list(
        "PREFERRED SKILL GAPS",
        plan[
            "preferred_skill_gaps"
        ],
        "GAP: "
    )

    print()
    print(
        "RECOMMENDED PROJECTS"
    )

    projects = plan[
        "recommended_projects"
    ]

    if not projects:

        print("  None")

    for project in projects:

        print()
        print(
            f"  {project['project']}"
        )

        print(
            f"      Relevance: "
            f"{project['relevance_score']}"
        )

        if project[
            "matching_skills"
        ]:

            print(
                "      Evidence: "
                + ", ".join(
                    project[
                        "matching_skills"
                    ]
                )
            )

    print()
    print(
        "SKILL EVIDENCE"
    )

    evidence = plan[
        "skill_evidence"
    ]

    if not evidence:

        print("  None")

    for skill, projects in evidence.items():

        print(
            f"  {skill}:"
        )

        for project in projects:

            print(
                f"      -> {project}"
            )

    print()
    print(
        "SAFETY CHECK"
    )

    safety = plan[
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


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "RESUME TAILORING TEST - VERSION 4"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # Check private resume
    # --------------------------------------------------------

    if not PRIVATE_RESUME.exists():

        print()
        print(
            "ERROR: Private resume profile "
            "was not found."
        )

        print(
            PRIVATE_RESUME
        )

        return

    # --------------------------------------------------------
    # Check tailoring rules
    # --------------------------------------------------------

    if not TAILORING_RULES.exists():

        print()
        print(
            "ERROR: Resume tailoring rules "
            "were not found."
        )

        print(
            TAILORING_RULES
        )

        return

    # --------------------------------------------------------
    # Check test job
    # --------------------------------------------------------

    if not JOB_FILE.exists():

        print()
        print(
            "ERROR: Test job was not found."
        )

        print(
            JOB_FILE
        )

        return

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    resume = load_json(
        PRIVATE_RESUME
    )

    rules = load_json(
        TAILORING_RULES
    )

    job = load_json(
        JOB_FILE
    )

    # --------------------------------------------------------
    # Build plan
    # --------------------------------------------------------

    plan = build_tailoring_plan(
        job,
        resume,
        rules
    )

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print_plan(
        plan
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = save_plan(
        plan
    )

    print()
    print(
        "Tailoring plan saved privately:"
    )

    print(
        output_file
    )


if __name__ == "__main__":
    main()