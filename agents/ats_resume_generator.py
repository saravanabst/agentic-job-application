import json
from pathlib import Path

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


BASE_DIR = Path(__file__).resolve().parent.parent

PRIVATE_RESUME = (
    BASE_DIR
    / "resumes"
    / "private"
    / "resume_profile.json"
)

TAILORING_PLAN = (
    BASE_DIR
    / "resumes"
    / "private"
    / "tailoring"
    / "job_001_tailoring_plan.json"
)

OUTPUT_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
)


def load_json(file_path):
    """Load JSON file."""

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def setup_document():
    """Create an ATS-friendly Word document."""

    document = Document()

    section = document.sections[0]

    section.top_margin = Inches(0.55)
    section.bottom_margin = Inches(0.55)
    section.left_margin = Inches(0.65)
    section.right_margin = Inches(0.65)

    styles = document.styles

    normal = styles["Normal"]

    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(
        qn("w:eastAsia"),
        "Arial"
    )
    normal.font.size = Pt(9.5)

    return document


def add_text(
    document,
    text,
    bold=False,
    size=9.5,
    alignment=None,
    space_after=2
):
    """Add standard ATS-safe paragraph."""

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.space_after = Pt(
        space_after
    )

    paragraph.paragraph_format.line_spacing = 1.0

    if alignment is not None:
        paragraph.alignment = alignment

    run = paragraph.add_run(
        str(text)
    )

    run.bold = bold
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(
        qn("w:eastAsia"),
        "Arial"
    )
    run.font.size = Pt(size)

    return paragraph


def add_heading(
    document,
    text
):
    """Add ATS-friendly section heading."""

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(3)

    run = paragraph.add_run(
        text.upper()
    )

    run.bold = True
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(
        qn("w:eastAsia"),
        "Arial"
    )
    run.font.size = Pt(11)

    return paragraph


def add_bullet(
    document,
    text
):
    """Add simple ATS-safe bullet."""

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.left_indent = Inches(
        0.18
    )

    paragraph.paragraph_format.first_line_indent = Inches(
        -0.12
    )

    paragraph.paragraph_format.space_after = Pt(
        2
    )

    paragraph.paragraph_format.line_spacing = 1.0

    run = paragraph.add_run(
        "• " + str(text)
    )

    run.font.name = "Arial"
    run._element.rPr.rFonts.set(
        qn("w:eastAsia"),
        "Arial"
    )
    run.font.size = Pt(9.5)

    return paragraph


def add_label_value(
    document,
    label,
    value
):
    """Add a labelled line."""

    paragraph = document.add_paragraph()

    paragraph.paragraph_format.space_after = Pt(2)

    label_run = paragraph.add_run(
        label
    )

    label_run.bold = True
    label_run.font.name = "Arial"
    label_run.font.size = Pt(9.5)

    value_run = paragraph.add_run(
        str(value)
    )

    value_run.font.name = "Arial"
    value_run.font.size = Pt(9.5)

    return paragraph


def build_professional_summary(
    resume,
    tailoring
):
    """Build conservative job-targeted summary."""

    summary_data = resume.get(
        "professional_summary",
        {}
    )

    base_summary = summary_data.get(
        "summary",
        ""
    )

    matched_required = tailoring.get(
        "matched_required_skills",
        []
    )

    matched_preferred = tailoring.get(
        "matched_preferred_skills",
        []
    )

    matched = (
        matched_required
        + matched_preferred
    )

    if matched:

        skills_text = ", ".join(
            matched
        )

        return (
            base_summary
            + " Experienced in applying "
            + skills_text
            + " through practical analytics "
              "and portfolio projects."
        )

    return base_summary


def get_project_map(resume):
    """Create project lookup."""

    project_map = {}

    for project in resume.get(
        "portfolio_projects",
        []
    ):

        project_map[
            project.get("name", "")
        ] = project

    return project_map


def select_projects(
    resume,
    tailoring
):
    """Select the strongest verified projects."""

    project_map = get_project_map(
        resume
    )

    recommendations = tailoring.get(
        "recommended_projects",
        []
    )

    selected = []

    for recommendation in recommendations:

        project_name = recommendation.get(
            "project",
            ""
        )

        project = project_map.get(
            project_name
        )

        if project:
            selected.append(
                (
                    project,
                    recommendation
                )
            )

    if selected:
        return selected

    return [
        (
            project,
            {
                "relevance_score": 0,
                "matching_skills": []
            }
        )
        for project in resume.get(
            "portfolio_projects",
            []
        )[:3]
    ]


def add_personal_header(
    document,
    resume
):
    """Add resume header."""

    personal = resume.get(
        "personal",
        {}
    )

    name = personal.get(
        "full_name",
        ""
    )

    paragraph = document.add_paragraph()

    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    paragraph.paragraph_format.space_after = Pt(
        2
    )

    run = paragraph.add_run(
        name
    )

    run.bold = True
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(
        qn("w:eastAsia"),
        "Arial"
    )
    run.font.size = Pt(16)

    target_role = resume.get(
        "professional_summary",
        {}
    ).get(
        "target_role",
        "Data Analyst"
    )

    add_text(
        document,
        target_role.upper(),
        bold=True,
        size=10,
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=3
    )

    contact_items = []

    if personal.get("email"):
        contact_items.append(
            "Email: "
            + personal["email"]
        )

    if personal.get("phone"):
        contact_items.append(
            "Phone: "
            + personal["phone"]
        )

    if personal.get("location"):
        contact_items.append(
            "Location: "
            + personal["location"]
        )

    if personal.get("linkedin_url"):
        contact_items.append(
            "LinkedIn: "
            + personal["linkedin_url"]
        )

    add_text(
        document,
        " | ".join(contact_items),
        size=8.5,
        alignment=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=5
    )


def add_professional_summary(
    document,
    resume,
    tailoring
):
    """Add professional summary."""

    add_heading(
        document,
        "Professional Summary"
    )

    summary = build_professional_summary(
        resume,
        tailoring
    )

    add_text(
        document,
        summary,
        size=9.5,
        space_after=4
    )


def add_core_skills(
    document,
    resume
):
    """Add keyword-rich core skills."""

    add_heading(
        document,
        "Core Skills"
    )

    skills = resume.get(
        "technical_skills",
        {}
    )

    categories = {
        "Business Analysis": [
            "Business Analysis",
            "Process Optimisation",
            "Continuous Improvement",
            "KPI Development",
            "Performance Monitoring",
            "Trend Analysis",
            "Root Cause Analysis",
            "Business Reporting"
        ],
        "Data Analytics": [
            "SQL",
            "MySQL",
            "Python",
            "Pandas",
            "NumPy",
            "Data Cleaning",
            "Data Validation",
            "Data Transformation",
            "Data Automation"
        ],
        "Business Intelligence": [
            "Tableau",
            "Advanced Excel",
            "PivotTables",
            "Dashboards",
            "KPI Reporting",
            "Data Visualisation",
            "Performance Analytics"
        ],
        "Professional Skills": [
            "Stakeholder Management",
            "Cross-functional Collaboration",
            "Problem Solving",
            "Communication",
            "Attention to Detail",
            "Project Coordination"
        ]
    }

    all_candidate_skills = set()

    for group in skills.values():

        for skill in group:
            all_candidate_skills.add(
                skill.lower()
            )

    for category, category_skills in categories.items():

        verified = []

        for skill in category_skills:

            if skill.lower() in all_candidate_skills:
                verified.append(skill)

        if verified:

            add_label_value(
                document,
                category + ": ",
                " • ".join(verified)
            )


def add_experience(
    document,
    resume
):
    """Add verified professional experience."""

    experience = resume.get(
        "experience",
        []
    )

    if not experience:
        return

    add_heading(
        document,
        "Professional Experience"
    )

    for role in experience:

        company = role.get(
            "company",
            ""
        )

        title = role.get(
            "job_title",
            ""
        )

        start = role.get(
            "start_date",
            ""
        )

        end = role.get(
            "end_date",
            ""
        )

        location = role.get(
            "location",
            ""
        )

        date_text = ""

        if start and end:
            date_text = (
                start
                + "–"
                + end
            )
        elif start:
            date_text = start

        header = title

        if company:
            header += (
                " | "
                + company
            )

        if date_text:
            header += (
                " | "
                + date_text
            )

        add_text(
            document,
            header,
            bold=True,
            size=10,
            space_after=1
        )

        if location:
            add_text(
                document,
                location,
                size=8.5,
                space_after=2
            )

        for responsibility in role.get(
            "responsibilities",
            []
        ):

            add_bullet(
                document,
                responsibility
            )

        for achievement in role.get(
            "achievements",
            []
        ):

            add_bullet(
                document,
                achievement
            )


def add_projects(
    document,
    resume,
    tailoring
):
    """Add selected data analytics projects."""

    add_heading(
        document,
        "Selected Data Analytics Projects"
    )

    selected_projects = select_projects(
        resume,
        tailoring
    )

    for project, recommendation in selected_projects:

        name = project.get(
            "name",
            ""
        )

        technologies = project.get(
            "technologies",
            []
        )

        title = name

        if technologies:

            title += (
                " | "
                + " | ".join(
                    technologies
                )
            )

        add_text(
            document,
            title,
            bold=True,
            size=10,
            space_after=2
        )

        for achievement in project.get(
            "achievements",
            []
        ):

            add_bullet(
                document,
                achievement
            )


def add_education(
    document,
    resume
):
    """Add education."""

    education = resume.get(
        "education",
        []
    )

    if not education:
        return

    add_heading(
        document,
        "Education"
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

        institution = item.get(
            "institution",
            ""
        )

        line = qualification

        if specialization:
            line += (
                " — "
                + specialization
            )

        add_text(
            document,
            line,
            bold=True,
            size=9.5,
            space_after=1
        )

        if institution:

            add_text(
                document,
                institution,
                size=9,
                space_after=3
            )


def add_technical_skills(
    document,
    resume
):
    """Add complete verified technical skills."""

    add_heading(
        document,
        "Technical Skills"
    )

    skills = resume.get(
        "technical_skills",
        {}
    )

    labels = {
        "programming": "Programming & Analytics",
        "databases": "Databases",
        "visualization": "Visualisation",
        "analytics": "Business Intelligence & Analytics",
        "machine_learning": "Machine Learning",
        "automation": "Automation",
        "development": "Development",
        "ai": "Artificial Intelligence"
    }

    for category, items in skills.items():

        if not items:
            continue

        label = labels.get(
            category,
            category.replace(
                "_",
                " "
            ).title()
        )

        add_label_value(
            document,
            label + ": ",
            " • ".join(items)
        )


def add_certifications(
    document,
    resume
):
    """Add certifications."""

    certifications = resume.get(
        "certifications",
        []
    )

    if not certifications:
        return

    add_heading(
        document,
        "Certifications"
    )

    add_text(
        document,
        " • ".join(
            certifications
        ),
        size=9.5
    )


def add_additional_information(
    document,
    resume
):
    """Add additional information."""

    information = resume.get(
        "additional_information",
        {}
    )

    add_heading(
        document,
        "Additional Information"
    )

    work_rights = resume.get(
        "personal",
        {}
    ).get(
        "work_rights",
        ""
    )

    if work_rights:
        add_bullet(
            document,
            work_rights
        )

    driving = information.get(
        "driving_license",
        ""
    )

    if driving:
        add_bullet(
            document,
            driving
        )

    location = resume.get(
        "personal",
        {}
    ).get(
        "location",
        ""
    )

    if location:
        add_bullet(
            document,
            "Based in "
            + location
        )

    interests = information.get(
        "interests",
        []
    )

    if interests:
        add_bullet(
            document,
            "Strong interest in "
            + ", ".join(interests)
        )


def add_safety_footer(
    document,
    tailoring
):
    """Add internal safety information only."""

    safety = {
        "invented_experience": False,
        "invented_skills": False,
        "invented_education": False,
        "invented_employment": False,
        "automatic_submission": False,
        "human_review_required": True
    }

    plan_safety = tailoring.get(
        "safety",
        {}
    )

    for key in safety:

        if key in plan_safety:
            safety[key] = plan_safety[key]

    return safety


def generate_resume(
    resume,
    tailoring
):
    """Generate ATS-friendly resume."""

    document = setup_document()

    add_personal_header(
        document,
        resume
    )

    add_professional_summary(
        document,
        resume,
        tailoring
    )

    add_core_skills(
        document,
        resume
    )

    add_experience(
        document,
        resume
    )

    add_projects(
        document,
        resume,
        tailoring
    )

    add_education(
        document,
        resume
    )

    add_technical_skills(
        document,
        resume
    )

    add_certifications(
        document,
        resume
    )

    add_additional_information(
        document,
        resume
    )

    return document


def main():

    print()
    print(
        "ATS RESUME GENERATOR TEST - VERSION 5"
    )
    print("=" * 60)

    if not PRIVATE_RESUME.exists():

        print(
            "ERROR: Resume profile not found:"
        )

        print(PRIVATE_RESUME)

        return

    if not TAILORING_PLAN.exists():

        print(
            "ERROR: Tailoring plan not found:"
        )

        print(TAILORING_PLAN)

        return

    resume = load_json(
        PRIVATE_RESUME
    )

    tailoring = load_json(
        TAILORING_PLAN
    )

    job = tailoring.get(
        "job",
        {}
    )

    print()
    print(
        "ATS RESUME GENERATOR"
    )
    print("=" * 60)

    print()
    print(
        f"Job:      "
        f"{job.get('title', '')}"
    )

    print(
        f"Company:  "
        f"{job.get('company', '')}"
    )

    print(
        f"Location: "
        f"{job.get('location', '')}"
    )

    print()
    print(
        "ATS FORMAT:"
    )

    print(
        "  Single-column layout"
    )

    print(
        "  Standard section headings"
    )

    print(
        "  No tables"
    )

    print(
        "  No text boxes"
    )

    print(
        "  No graphics"
    )

    print(
        "  No icons"
    )

    print(
        "  Standard Word document"
    )

    safety = add_safety_footer(
        None,
        tailoring
    )

    print()
    print(
        "SAFETY:"
    )

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
        f"  Automatic submission: "
        f"{safety['automatic_submission']}"
    )

    print(
        f"  Human review required: "
        f"{safety['human_review_required']}"
    )

    document = generate_resume(
        resume,
        tailoring
    )

    job_id = job.get(
        "job_id",
        "unknown"
    )

    job_output_dir = (
        OUTPUT_DIR
        / job_id
        / "tailored"
    )

    job_output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        job_output_dir
        / "resume.docx"
    )

    document.save(
        output_file
    )

    print()
    print(
        "Resume saved:"
    )

    print(output_file)


if __name__ == "__main__":
    main()