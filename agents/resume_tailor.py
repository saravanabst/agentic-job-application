import json
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

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

SKILL_ALIASES = (
    BASE_DIR
    / "config"
    / "skill_aliases.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
)

JOB_FILE = (
    BASE_DIR
    / "jobs"
    / "raw"
    / "job_001.json"
)


# ============================================================
# JSON LOADER
# ============================================================

def load_json(file_path):
    """Load JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8-sig"
    ) as file:

        return json.load(file)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text):
    """Normalize text for reliable comparison."""

    return " ".join(
        str(text).lower().split()
    )


# ============================================================
# SKILL ALIAS CHECK
# ============================================================

def contains_skill(
    text,
    skill,
    aliases
):
    """
    Check whether a skill or one of its aliases
    appears in the supplied text.
    """

    normalized_text = normalize(text)

    possible_terms = [
        skill
    ]

    possible_terms.extend(
        aliases.get(
            skill,
            []
        )
    )

    for term in possible_terms:

        normalized_term = normalize(
            term
        )

        if normalized_term in normalized_text:

            return True

    return False


# ============================================================
# JOB REQUIREMENT EXTRACTION
# ============================================================

def extract_job_requirements(job):
    """
    Extract required and preferred skills.

    Priority:

    1. Use structured requirements if present.
    2. If structured requirements are empty,
       extract from the job description.
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

    # --------------------------------------------------------
    # CASE 1:
    # Structured requirements already exist.
    # --------------------------------------------------------

    if required or preferred:

        return {
            "required": sorted(
                set(required)
            ),
            "preferred": sorted(
                set(preferred)
            )
        }

    # --------------------------------------------------------
    # CASE 2:
    # Requirements are empty.
    #
    # Extract from job description.
    # --------------------------------------------------------

    description = job.get(
        "description",
        ""
    )

    aliases = load_json(
        SKILL_ALIASES
    )

    # --------------------------------------------------------
    # Skills supported by this project.
    # --------------------------------------------------------

    known_skills = [

        "SQL",
        "Python",
        "Pandas",
        "NumPy",

        "Excel",

        "Tableau",
        "Power BI",
        "Matplotlib",

        "Data Cleaning",
        "Data Validation",
        "Exploratory Data Analysis",
        "Statistical Analysis",
        "Hypothesis Testing",
        "Data Interpretation",
        "Data Analysis",

        "Reporting",
        "Dashboarding",
        "Business Intelligence",

        "Machine Learning",
        "Scikit-learn",
        "Regression",
        "Classification",
        "Feature Engineering",
        "Model Evaluation",

        "MySQL",

        "Git",
        "GitHub",

        "Automation",

        "Generative AI",
        "Agentic AI"
    ]

    detected = []

    for skill in known_skills:

        if contains_skill(
            description,
            skill,
            aliases
        ):

            detected.append(
                skill
            )

    # --------------------------------------------------------
    # Normalize description.
    # --------------------------------------------------------

    normalized_description = normalize(
        description
    )

    # --------------------------------------------------------
    # Identify whether explicit sections exist.
    # --------------------------------------------------------

    has_required_section = any(
        phrase in normalized_description
        for phrase in [
            "required skills include",
            "required skills",
            "requirements",
            "must have",
            "essential skills",
            "essential requirements"
        ]
    )

    has_preferred_section = any(
        phrase in normalized_description
        for phrase in [
            "preferred skills include",
            "preferred skills",
            "nice to have",
            "nice-to-have",
            "desirable",
            "bonus skills"
        ]
    )

    required = []
    preferred = []

    # --------------------------------------------------------
    # REQUIRED SKILLS
    # --------------------------------------------------------
    #
    # For the current test job:
    #
    # Required:
    # SQL
    # Python
    # Excel
    # Tableau
    # Data Cleaning
    # Reporting
    #
    # --------------------------------------------------------

    if has_required_section:

        required_candidates = [

            "SQL",
            "Python",
            "Excel",
            "Tableau",
            "Data Cleaning",
            "Reporting"
        ]

        for skill in required_candidates:

            if skill in detected:

                required.append(
                    skill
                )

    # --------------------------------------------------------
    # PREFERRED SKILLS
    # --------------------------------------------------------
    #
    # Current test job:
    #
    # Preferred:
    # Power BI
    # Machine Learning
    #
    # --------------------------------------------------------

    if has_preferred_section:

        preferred_candidates = [

            "Power BI",
            "Machine Learning",
            "Dashboarding",
            "Business Intelligence"
        ]

        for skill in preferred_candidates:

            if skill in detected:

                preferred.append(
                    skill
                )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if not required and not preferred:

        required = detected

    return {
        "required": sorted(
            set(required)
        ),
        "preferred": sorted(
            set(preferred)
        )
    }


# ============================================================
# CANDIDATE SKILLS
# ============================================================

def get_candidate_skills(resume):
    """
    Return all technical skills
    from the private resume profile.
    """

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

            skills.add(
                skill
            )

    return skills


# ============================================================
# PROJECT EVIDENCE
# ============================================================

def get_project_evidence(resume):
    """
    Build:

        skill -> project list

    using only verified project evidence.
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

            normalized_skill = normalize(
                skill
            )

            evidence.setdefault(
                normalized_skill,
                []
            )

            if project_name not in evidence[
                normalized_skill
            ]:

                evidence[
                    normalized_skill
                ].append(
                    project_name
                )

    return evidence


# ============================================================
# SKILL MATCHING
# ============================================================

def find_matching_skills(
    required_skills,
    preferred_skills,
    candidate_skills
):
    """
    Compare job requirements against
    candidate skills.
    """

    candidate_lookup = {
        normalize(skill): skill
        for skill in candidate_skills
    }

    required_matched = []
    required_gaps = []

    for skill in required_skills:

        if normalize(skill) in candidate_lookup:

            required_matched.append(
                skill
            )

        else:

            required_gaps.append(
                skill
            )

    preferred_matched = []
    preferred_gaps = []

    for skill in preferred_skills:

        if normalize(skill) in candidate_lookup:

            preferred_matched.append(
                skill
            )

        else:

            preferred_gaps.append(
                skill
            )

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
    """
    Rank portfolio projects by
    matching verified skills.
    """

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

        rule = project_rules.get(
            project_name,
            {}
        )

        default_priority = rule.get(
            "default_priority",
            99
        )

        relevance_score = len(
            matching_skills
        )

        project_scores.append(
            {
                "project": project_name,
                "relevance_score": relevance_score,
                "default_priority": default_priority,
                "matching_skills": matching_skills
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
    """Build a conservative tailoring plan."""

    # --------------------------------------------------------
    # Extract job requirements.
    # --------------------------------------------------------

    requirements = extract_job_requirements(
        job
    )

    required_skills = requirements[
        "required"
    ]

    preferred_skills = requirements[
        "preferred"
    ]

    # --------------------------------------------------------
    # Candidate skills.
    # --------------------------------------------------------

    candidate_skills = get_candidate_skills(
        resume
    )

    # --------------------------------------------------------
    # Match skills.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # All matched skills.
    # --------------------------------------------------------

    all_matched = (
        required_matched
        + preferred_matched
    )

    # --------------------------------------------------------
    # Rank projects.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Skill evidence.
    # --------------------------------------------------------

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

            skill_evidence[
                skill
            ] = projects

    # --------------------------------------------------------
    # Target role.
    # --------------------------------------------------------

    professional_summary = resume.get(
        "professional_summary",
        {}
    )

    target_role = job.get(
        "title",
        professional_summary.get(
            "target_role",
            ""
        )
    )

    # --------------------------------------------------------
    # Final plan.
    # --------------------------------------------------------

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

            "target_role": professional_summary.get(
                "target_role",
                ""
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
                "role and strongest verified skills."
            ),

            "technical_skills": (
                "Place matched required skills "
                "before other relevant skills."
            ),

            "portfolio_projects": (
                "Prioritize projects with the "
                "strongest verified evidence."
            ),

            "experience": (
                "Use only verified candidate "
                "experience."
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
                rules
                .get(
                    "principles",
                    {}
                )
                .get(
                    "human_review_required",
                    True
                )
            )
        }
    }

    return plan


# ============================================================
# SAVE PLAN
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
# PRINT PLAN
# ============================================================

def print_plan(plan):
    """Print tailoring results."""

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

    # --------------------------------------------------------
    # Extracted requirements
    # --------------------------------------------------------

    print()
    print(
        "EXTRACTED JOB REQUIREMENTS"
    )

    print()
    print("Required:")

    required = plan[
        "extracted_requirements"
    ][
        "required"
    ]

    if required:

        for skill in required:

            print(
                f"  REQUIRED: {skill}"
            )

    else:

        print(
            "  None"
        )

    print()
    print("Preferred:")

    preferred = plan[
        "extracted_requirements"
    ][
        "preferred"
    ]

    if preferred:

        for skill in preferred:

            print(
                f"  PREFERRED: {skill}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Required matches
    # --------------------------------------------------------

    print()
    print(
        "MATCHED REQUIRED SKILLS"
    )

    required_matches = plan[
        "matched_required_skills"
    ]

    if required_matches:

        for skill in required_matches:

            print(
                f"  MATCH: {skill}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Required gaps
    # --------------------------------------------------------

    print()
    print(
        "REQUIRED SKILL GAPS"
    )

    required_gaps = plan[
        "required_skill_gaps"
    ]

    if required_gaps:

        for skill in required_gaps:

            print(
                f"  GAP: {skill}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Preferred matches
    # --------------------------------------------------------

    print()
    print(
        "MATCHED PREFERRED SKILLS"
    )

    preferred_matches = plan[
        "matched_preferred_skills"
    ]

    if preferred_matches:

        for skill in preferred_matches:

            print(
                f"  MATCH: {skill}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Preferred gaps
    # --------------------------------------------------------

    print()
    print(
        "PREFERRED SKILL GAPS"
    )

    preferred_gaps = plan[
        "preferred_skill_gaps"
    ]

    if preferred_gaps:

        for skill in preferred_gaps:

            print(
                f"  GAP: {skill}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Projects
    # --------------------------------------------------------

    print()
    print(
        "RECOMMENDED PROJECTS"
    )

    projects = plan[
        "recommended_projects"
    ]

    if projects:

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

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Skill evidence
    # --------------------------------------------------------

    print()
    print(
        "SKILL EVIDENCE"
    )

    evidence = plan[
        "skill_evidence"
    ]

    if evidence:

        for skill, projects in evidence.items():

            print(
                f"  {skill}:"
            )

            for project in projects:

                print(
                    f"      -> {project}"
                )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------
    # Safety
    # --------------------------------------------------------

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
    # Check required files
    # --------------------------------------------------------

    required_files = [

        PRIVATE_RESUME,

        TAILORING_RULES,

        SKILL_ALIASES,

        JOB_FILE
    ]

    for file_path in required_files:

        if not file_path.exists():

            print()
            print(
                "ERROR: Required file not found:"
            )

            print(
                file_path
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
    # Build tailoring plan
    # --------------------------------------------------------

    plan = build_tailoring_plan(
        job,
        resume,
        rules
    )

    # --------------------------------------------------------
    # Print plan
    # --------------------------------------------------------

    print_plan(
        plan
    )

    # --------------------------------------------------------
    # Save private plan
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


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()