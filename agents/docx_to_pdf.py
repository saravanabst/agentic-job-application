import sys
import subprocess
from pathlib import Path


# ============================================================
# DOCX -> PDF CONVERSION AGENT
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

JOB_ID = sys.argv[1] if len(sys.argv) > 1 else "job_001"

OUTPUT_DIR = (
    BASE_DIR
    / "resumes"
    / "output"
    / JOB_ID
)

RESUME_DOCX = (
    OUTPUT_DIR
    / "tailored"
    / "resume.docx"
)

COVER_LETTER_DOCX = (
    OUTPUT_DIR
    / "cover_letter"
    / "cover_letter.docx"
)

RESUME_PDF = (
    OUTPUT_DIR
    / "tailored"
    / "resume.pdf"
)

COVER_LETTER_PDF = (
    OUTPUT_DIR
    / "cover_letter"
    / "cover_letter.pdf"
)

LIBREOFFICE_CANDIDATES = [
    Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
    Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
]


# ============================================================
# FIND LIBREOFFICE
# ============================================================

def find_libreoffice():

    for executable in LIBREOFFICE_CANDIDATES:

        if executable.exists():
            return executable

    return None


# ============================================================
# CONVERT DOCX
# ============================================================

def convert_docx_to_pdf(docx_file, output_dir):

    libreoffice = find_libreoffice()

    if libreoffice is None:

        print()
        print("ERROR: LibreOffice executable was not found.")
        print()
        return False

    if not docx_file.exists():

        print()
        print("ERROR: DOCX file is missing:")
        print(docx_file)
        print()

        return False

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    command = [
        str(libreoffice),
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(docx_file),
    ]

    print()
    print("Converting:")
    print(docx_file)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print()
        print("ERROR: LibreOffice conversion failed.")
        print(result.stderr)

        return False

    pdf_file = (
        output_dir
        / f"{docx_file.stem}.pdf"
    )

    if not pdf_file.exists():

        print()
        print("ERROR: PDF was not created.")
        print(pdf_file)

        return False

    if pdf_file.stat().st_size == 0:

        print()
        print("ERROR: PDF was created but is empty.")
        print(pdf_file)

        return False

    print()
    print("PDF created:")
    print(pdf_file)

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("DOCX TO PDF CONVERTER - VERSION 1")
    print("=" * 60)

    print()
    print("JOB ID:")
    print(JOB_ID)

    libreoffice = find_libreoffice()

    print()
    print("LIBREOFFICE:")

    if libreoffice:
        print(libreoffice)
    else:
        print("NOT FOUND")

    if libreoffice is None:
        return False

    print()
    print("CONVERTING RESUME")

    resume_success = convert_docx_to_pdf(
        RESUME_DOCX,
        RESUME_DOCX.parent
    )

    print()
    print("CONVERTING COVER LETTER")

    cover_letter_success = convert_docx_to_pdf(
        COVER_LETTER_DOCX,
        COVER_LETTER_DOCX.parent
    )

    print()
    print("=" * 60)

    if resume_success and cover_letter_success:

        print("DOCX TO PDF CONVERSION COMPLETE")
        print()
        print("Resume PDF:")
        print(RESUME_PDF)
        print()
        print("Cover Letter PDF:")
        print(COVER_LETTER_PDF)

        return True

    print("DOCX TO PDF CONVERSION FAILED")

    return False


if __name__ == "__main__":

    success = main()

    sys.exit(
        0 if success else 1
    )
