from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "example"

PERSON = {
    "full_name": "Maya Chen",
    "email": "maya.chen.sim@example.com",
    "linkedin": "www.linkedin.com/in/maya-chen-sim",
    "github": "https://github.com/mayachen-sim",
    "permanent_address": "Irvine, California, United States, 92617",
    "permanent_phone": "+1 (949) 555-0134",
    "current_address": "New York, New York, United States, 10027",
    "current_phone": "+1 (917) 555-0198",
}

SCHOOLS = [
    {
        "filename": "SIM-University-of-California-Irvine-Transcript.docx",
        "institution": "University of California, Irvine",
        "location": "Irvine, California, United States",
        "student_id": "SIM-UCI-219044",
        "program": "Bachelor of Science in Mathematics",
        "period": "September 2019 - May 2021",
        "gpa": "3.89/4.00",
        "honors": [
            "Dean's Honor List (Spring 2020)",
            "Transfer Academic Excellence Scholarship (2021)",
        ],
        "terms": [
            {
                "name": "Fall 2019",
                "gpa": "3.84",
                "courses": [
                    ("MATH 2A", "Single-Variable Calculus", "4.00", "A"),
                    ("I&C SCI 31", "Introduction to Programming", "4.00", "A-"),
                    ("WRITING 39A", "Introduction to Writing and Rhetoric", "4.00", "A"),
                    ("ECON 20A", "Basic Economics", "4.00", "B+"),
                ],
            },
            {
                "name": "Spring 2020",
                "gpa": "3.95",
                "courses": [
                    ("MATH 2B", "Single-Variable Calculus II", "4.00", "A"),
                    ("STATS 7", "Basic Statistics", "4.00", "A"),
                    ("I&C SCI 32", "Programming with Software Libraries", "4.00", "A-"),
                    ("PHILOS 4", "Critical Reasoning", "4.00", "A"),
                ],
            },
            {
                "name": "Fall 2020",
                "gpa": "3.90",
                "courses": [
                    ("MATH 3A", "Introduction to Linear Algebra", "4.00", "A"),
                    ("I&C SCI 45C", "Programming in C/C++ as a Second Language", "4.00", "A-"),
                    ("PHYSICS 7C", "Classical Physics", "4.00", "B+"),
                    ("MGT 1", "Introduction to Business and Management", "4.00", "A"),
                ],
            },
            {
                "name": "Spring 2021",
                "gpa": "3.86",
                "courses": [
                    ("MATH 140A", "Elementary Analysis", "4.00", "A-"),
                    ("MATH 130A", "Introduction to Probability", "4.00", "A"),
                    ("ICS 6D", "Discrete Mathematics for Computer Science", "4.00", "A-"),
                    ("PSYCH 10A", "Research Methods", "4.00", "A"),
                ],
            },
        ],
    },
    {
        "filename": "SIM-Northeastern-University-Transcript.docx",
        "institution": "Northeastern University",
        "location": "Boston, Massachusetts, United States",
        "student_id": "SIM-NEU-440182",
        "program": "Bachelor of Science in Data Science",
        "period": "September 2021 - May 2024",
        "gpa": "3.92/4.00",
        "honors": [
            "Dean's List (Fall 2022)",
            "Undergraduate Research Award (2023)",
            "High Distinction (May 2024)",
        ],
        "terms": [
            {
                "name": "Fall 2021",
                "gpa": "3.88",
                "courses": [
                    ("DS 3000", "Foundations of Data Science", "4.00", "A"),
                    ("CS 3200", "Database Design", "4.00", "A-"),
                    ("MATH 3081", "Probability and Statistics", "4.00", "A"),
                    ("ENGW 3302", "Advanced Writing in the Disciplines", "4.00", "A-"),
                ],
            },
            {
                "name": "Spring 2022",
                "gpa": "3.95",
                "courses": [
                    ("DS 3500", "Advanced Programming with Data", "4.00", "A"),
                    ("DS 4200", "Information Presentation and Visualization", "4.00", "A"),
                    ("MATH 4570", "Applied Probability and Statistics", "4.00", "A-"),
                    ("CS 5800", "Algorithms", "4.00", "A"),
                ],
            },
            {
                "name": "Fall 2022",
                "gpa": "4.00",
                "courses": [
                    ("DS 4300", "Large-Scale Information Storage and Retrieval", "4.00", "A"),
                    ("DS 4400", "Machine Learning and Data Mining 1", "4.00", "A"),
                    ("DS 4440", "Practical Neural Networks", "4.00", "A"),
                    ("MATH 4681", "Numerical Analysis 1", "4.00", "A"),
                ],
            },
            {
                "name": "Spring 2023",
                "gpa": "3.93",
                "courses": [
                    ("DS 4420", "Machine Learning and Data Mining 2", "4.00", "A"),
                    ("DS 4600", "Knowledge in a Digital World", "4.00", "A-"),
                    ("CS 4100", "Artificial Intelligence", "4.00", "A-"),
                    ("MATH 4581", "Statistics and Stochastic Processes", "4.00", "A"),
                ],
            },
        ],
    },
    {
        "filename": "SIM-Columbia-University-Transcript.docx",
        "institution": "Columbia University",
        "location": "New York, New York, United States",
        "student_id": "SIM-CU-551207",
        "program": "Master of Arts in Statistics",
        "period": "September 2025 - February 2027",
        "gpa": "3.78/4.00",
        "honors": ["Merit Fellowship (2025)"],
        "terms": [
            {
                "name": "Fall 2025",
                "gpa": "3.76",
                "courses": [
                    ("STAT GU4203", "Applied Linear Regression Analysis", "3.00", "A-"),
                    ("STAT GU4204", "Statistical Inference", "3.00", "A"),
                    ("COMS W4721", "Machine Learning for Data Science", "3.00", "A-"),
                    ("IEOR E4404", "Simulation", "3.00", "A"),
                ],
            },
            {
                "name": "Spring 2026",
                "gpa": "3.80",
                "courses": [
                    ("STAT GU4207", "Probability Theory", "3.00", "A"),
                    ("STAT GR5263", "Applied Data Science", "3.00", "A-"),
                    ("IEOR E6711", "Optimization Models and Methods", "3.00", "A"),
                    ("COMS W4995", "Large-Scale Deep Learning", "3.00", "A-"),
                ],
            },
        ],
    },
]

INTERNSHIP_A = {
    "filename": "SIM-Amazon-Web-Services-Internship-Certificate.docx",
    "company": "Amazon Web Services, Inc.",
    "location": "Seattle, Washington, United States",
    "role": "Data Science Intern",
    "period": "June 5, 2023 - August 25, 2023",
    "content": (
        "Developed a customer retention dashboard and a churn scoring workflow for a cloud "
        "services subscription portfolio."
    ),
    "method": (
        "Built SQL and Python pipelines to clean CRM exports, engineer cohort features, and "
        "train logistic regression and gradient boosting models for renewal prediction."
    ),
    "result": (
        "Reduced weekly manual reporting time by 8 hours and improved pilot churn intervention "
        "precision from 0.41 to 0.63."
    ),
    "manager": "Erica Huang",
    "manager_title": "Director of Data Science",
    "manager_email": "erica.huang@aws-sim.example.com",
}

INTERNSHIP_B = {
    "filename": "SIM-Microsoft-Corporation-Internship-Certificate.docx",
    "company": "Microsoft Corporation",
    "location": "Redmond, Washington, United States",
    "role": "Machine Learning Intern",
    "period": "June 10, 2024 - August 30, 2024",
    "content": (
        "Developed a document classification and retrieval workflow for internal research archives."
    ),
    "method": (
        "Built evaluation pipelines with sentence embeddings, reranking, and prompt-based "
        "labeling to compare retrieval quality across multiple configurations."
    ),
    "result": (
        "Improved top-5 retrieval accuracy from 68 percent to 84 percent and shortened analyst "
        "review cycles by 30 percent."
    ),
    "manager": "Noah Patel",
    "manager_title": "Research Engineering Lead",
    "manager_email": "noah.patel@microsoft-sim.example.com",
}

RESUME_ACTIVITIES = [
    ("Graduate Student Mentor, Columbia University", "September 2025 - Present"),
    ("Volunteer Data Tutor, New York Public Library", "January 2023 - Present"),
]

DISCLAIMER = (
    "This document is fully simulated for software testing. The named schools and companies in "
    "this file are real organizations, but all student details, employment details, dates, "
    "grades, and narratives are fictional."
)


def set_run_font(run, size: float | None = None, bold: bool | None = None) -> None:
    run.font.name = "Arial"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def configure_document(document: Document, top: float, bottom: float, left: float, right: float) -> None:
    section = document.sections[0]
    section.top_margin = Inches(top)
    section.bottom_margin = Inches(bottom)
    section.left_margin = Inches(left)
    section.right_margin = Inches(right)
    style = document.styles["Normal"]
    style.font.name = "Arial"
    style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    style.font.size = Pt(10)


def add_paragraph(
    document: Document,
    text: str = "",
    *,
    bold: bool = False,
    size: float = 10,
    align: WD_ALIGN_PARAGRAPH | None = None,
    space_after: float = 3,
    space_before: float = 0,
) -> None:
    paragraph = document.add_paragraph()
    if align is not None:
        paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(space_after)
    paragraph.paragraph_format.space_before = Pt(space_before)
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)


def add_label_value_line(document: Document, label: str, value: str, *, size: float = 10) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(2)
    label_run = paragraph.add_run(f"{label}: ")
    set_run_font(label_run, size=size, bold=True)
    value_run = paragraph.add_run(value)
    set_run_font(value_run, size=size)


def set_cell_text(cell, text: str, *, bold: bool = False, align: WD_ALIGN_PARAGRAPH | None = None) -> None:
    paragraph = cell.paragraphs[0]
    paragraph.clear()
    if align is not None:
        paragraph.alignment = align
    run = paragraph.add_run(text)
    set_run_font(run, size=9.5, bold=bold)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP


def add_paragraph_bottom_border(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    p_bdr.append(bottom)


def remove_table_borders(table) -> None:
    table_pr = table._tbl.tblPr
    borders = table_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        table_pr.append(borders)
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:val"), "nil")
        borders.append(element)


def add_section_heading(document: Document, title: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(8)
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run(title)
    set_run_font(run, size=10.5, bold=True)
    add_paragraph_bottom_border(paragraph)


def add_resume_entry(document: Document, left_text: str, right_text: str) -> None:
    table = document.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    remove_table_borders(table)
    left_cell, right_cell = table.rows[0].cells
    left_cell.width = Inches(5.35)
    right_cell.width = Inches(1.75)
    set_cell_text(left_cell, left_text, bold=True)
    set_cell_text(right_cell, right_text, align=WD_ALIGN_PARAGRAPH.RIGHT)


def add_bullet_line(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(1)
    run = paragraph.add_run(text)
    set_run_font(run, size=9.3)


def lowercase_first_letter(text: str) -> str:
    for index, character in enumerate(text):
        if character.isalpha():
            return text[:index] + character.lower() + text[index + 1 :]
    return text


def build_transcript_docx(output_path: Path, school: dict) -> None:
    document = Document()
    configure_document(document, top=0.55, bottom=0.55, left=0.65, right=0.65)

    add_paragraph(
        document,
        "SIMULATED OFFICIAL TRANSCRIPT",
        bold=True,
        size=15,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_label_value_line(document, "Student", PERSON["full_name"])
    add_label_value_line(document, "Institution", school["institution"])
    add_label_value_line(document, "Location", school["location"])
    add_label_value_line(document, "Student ID", school["student_id"])
    add_label_value_line(document, "Program", school["program"])
    add_label_value_line(document, "Attendance Period", school["period"])
    add_label_value_line(document, "Cumulative GPA", school["gpa"])
    add_label_value_line(document, "Honors", ", ".join(school["honors"]))

    for term in school["terms"]:
        add_section_heading(document, term["name"])
        add_label_value_line(document, "Term GPA", term["gpa"], size=9.5)
        table = document.add_table(rows=1, cols=4)
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        header = table.rows[0].cells
        set_cell_text(header[0], "Course Code", bold=True)
        set_cell_text(header[1], "Course Title", bold=True)
        set_cell_text(header[2], "Credits", bold=True)
        set_cell_text(header[3], "Grade", bold=True)
        header[0].width = Inches(1.35)
        header[1].width = Inches(3.8)
        header[2].width = Inches(0.9)
        header[3].width = Inches(0.9)
        for code, title, credits, grade in term["courses"]:
            row = table.add_row().cells
            set_cell_text(row[0], code)
            set_cell_text(row[1], title)
            set_cell_text(row[2], credits, align=WD_ALIGN_PARAGRAPH.CENTER)
            set_cell_text(row[3], grade, align=WD_ALIGN_PARAGRAPH.CENTER)

    add_paragraph(document, DISCLAIMER, size=8.5, space_before=8)
    document.save(output_path)


def build_internship_certificate_docx(output_path: Path, internship: dict) -> None:
    document = Document()
    configure_document(document, top=0.75, bottom=0.75, left=0.8, right=0.8)

    add_paragraph(
        document,
        internship["company"],
        bold=True,
        size=15,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_paragraph(
        document,
        "Internship Verification Letter",
        bold=True,
        size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_label_value_line(document, "Office Location", internship["location"])
    add_paragraph(
        document,
        (
            f"This letter confirms that {PERSON['full_name']} completed a full-time internship at "
            f"{internship['company']} as a {internship['role']} from {internship['period']}."
        ),
        size=10.2,
    )
    add_paragraph(document, "During the internship, the following work was completed:", size=10.2)
    add_bullet_line(document, internship["content"])
    add_bullet_line(document, internship["method"])
    add_bullet_line(document, internship["result"])
    add_paragraph(
        document,
        (
            f"If further confirmation is needed, please contact {internship['manager']}, "
            f"{internship['manager_title']}, at {internship['manager_email']}."
        ),
        size=10.2,
        space_before=6,
    )
    add_paragraph(document, "Sincerely,", size=10.2, space_before=12, space_after=2)
    add_paragraph(document, internship["manager"], size=10.2, space_after=1)
    add_paragraph(document, internship["manager_title"], size=10.2, space_after=1)
    add_paragraph(document, internship["company"], size=10.2, space_after=1)
    add_paragraph(document, DISCLAIMER, size=8.5, space_before=12)
    document.save(output_path)


def build_recommendation_letter_docx(output_path: Path, internship: dict) -> None:
    document = Document()
    configure_document(document, top=0.75, bottom=0.75, left=0.8, right=0.8)

    add_paragraph(
        document,
        internship["company"],
        bold=True,
        size=15,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_paragraph(
        document,
        "Recommendation Letter",
        bold=True,
        size=11,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=8,
    )
    add_label_value_line(document, "Office Location", internship["location"])
    add_paragraph(document, "To Whom It May Concern,", size=10.2, space_after=8)
    add_paragraph(
        document,
        (
            f"I am pleased to recommend {PERSON['full_name']}, who worked with our team at "
            f"{internship['company']} as a {internship['role']} from {internship['period']}. "
            f"During this period, Maya consistently showed curiosity, strong execution, and "
            f"a high level of ownership."
        ),
        size=10.2,
    )
    add_paragraph(
        document,
        (
            f"In this role, Maya {lowercase_first_letter(internship['content'])} "
            f"She {lowercase_first_letter(internship['method'])}"
        ),
        size=10.2,
    )
    add_paragraph(
        document,
        (
            f"Most importantly, Maya delivered measurable results. Her work "
            f"{lowercase_first_letter(internship['result'])} She communicated clearly with analysts and "
            f"product stakeholders, documented her work carefully, and responded well to "
            f"feedback throughout the internship."
        ),
        size=10.2,
    )
    add_paragraph(
        document,
        (
            "I am confident that Maya will contribute strongly in future academic and "
            "professional settings, especially in data science, applied machine learning, "
            "and product-facing analytics work."
        ),
        size=10.2,
    )
    add_paragraph(document, "Sincerely,", size=10.2, space_before=12, space_after=2)
    add_paragraph(document, internship["manager"], size=10.2, space_after=1)
    add_paragraph(document, internship["manager_title"], size=10.2, space_after=1)
    add_paragraph(document, internship["company"], size=10.2, space_after=1)
    add_paragraph(document, internship["manager_email"], size=10.2, space_after=1)
    add_paragraph(document, DISCLAIMER, size=8.5, space_before=12)
    document.save(output_path)


def build_resume_docx(output_path: Path) -> None:
    document = Document()
    configure_document(document, top=0.4, bottom=0.45, left=0.5, right=0.5)

    add_paragraph(
        document,
        PERSON["full_name"],
        bold=True,
        size=16,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_paragraph(
        document,
        f"{PERSON['email']} | {PERSON['linkedin']} | {PERSON['github']}",
        size=9.6,
        align=WD_ALIGN_PARAGRAPH.CENTER,
        space_after=2,
    )
    add_paragraph(
        document,
        f"Permanent Address: {PERSON['permanent_address']} | {PERSON['permanent_phone']}",
        size=9.2,
        space_after=1,
    )
    add_paragraph(
        document,
        f"Current Address: {PERSON['current_address']} | {PERSON['current_phone']}",
        size=9.2,
        space_after=4,
    )

    add_section_heading(document, "EDUCATION")
    education_rows = [
        (
            "Columbia University, New York, NY, United States",
            "September 2025 - February 2027",
            "Master of Arts (expected Feb. 2027)",
            "Statistics | CGPA: 3.78/4.00 | Merit Fellowship (2025)",
        ),
        (
            "Northeastern University, Boston, MA, United States",
            "September 2021 - May 2024",
            "Bachelor of Science with High Distinction",
            "Data Science Major | Mathematics Minor | CGPA: 3.92/4.00 | Dean's List (Fall 2022)",
        ),
        (
            "University of California, Irvine, Irvine, CA, United States",
            "September 2019 - May 2021",
            "Bachelor of Science coursework prior to transfer",
            "Mathematics | CGPA: 3.89/4.00 | Transfer Academic Excellence Scholarship (2021)",
        ),
    ]
    for school_name, dates, degree_line, detail_line in education_rows:
        add_resume_entry(document, school_name, dates)
        add_paragraph(document, degree_line, bold=True, size=9.2, space_after=1)
        add_paragraph(document, detail_line, size=9.2, space_after=2)

    add_section_heading(document, "PROFESSIONAL EXPERIENCE")
    experience_rows = [
        {
            "company": "Microsoft Corporation, Redmond, WA, United States",
            "dates": "June 2024 - August 2024",
            "title": "Machine Learning Intern",
            "bullets": [
                "Developed a document classification and retrieval workflow for internal research archives.",
                "Built evaluation pipelines with sentence embeddings, reranking, and prompt-based labeling to compare retrieval quality across multiple configurations.",
                "Improved top-5 retrieval accuracy from 68 percent to 84 percent and shortened analyst review cycles by 30 percent.",
            ],
        },
        {
            "company": "Amazon Web Services, Inc., Seattle, WA, United States",
            "dates": "June 2023 - August 2023",
            "title": "Data Science Intern",
            "bullets": [
                "Developed a customer retention dashboard and a churn scoring workflow for a cloud services subscription portfolio.",
                "Built SQL and Python pipelines to clean CRM exports, engineer cohort features, and train logistic regression and gradient boosting models for renewal prediction.",
                "Reduced weekly manual reporting time by 8 hours and improved pilot churn intervention precision from 0.41 to 0.63.",
            ],
        },
    ]
    for item in experience_rows:
        add_resume_entry(document, item["company"], item["dates"])
        add_paragraph(document, item["title"], bold=True, size=9.2, space_after=1)
        for bullet in item["bullets"]:
            add_bullet_line(document, bullet)

    add_section_heading(document, "SKILLS")
    add_paragraph(document, "Languages: English (Fluent), Mandarin (Native)", size=9.2, space_after=1)
    add_paragraph(
        document,
        (
            "Computer: Python, R, SQL, Git, Docker, pandas, NumPy, scikit-learn, PyTorch, "
            "large language model, retrieval-augmented generation, linear regression, "
            "machine learning"
        ),
        size=9.2,
        space_after=1,
    )
    add_paragraph(
        document,
        (
            "Mathematical Background: Calculus, Linear Algebra, Probability Theory, "
            "Statistical Inference, Bayesian Statistics, Optimization, Time Series Analysis, "
            "Causal Inference"
        ),
        size=9.2,
        space_after=2,
    )

    add_section_heading(document, "ACTIVITIES")
    for role, dates in RESUME_ACTIVITIES:
        add_resume_entry(document, role, dates)

    add_paragraph(document, DISCLAIMER, size=8.5, space_before=10)
    document.save(output_path)


def clear_existing_simulated_files() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in OUTPUT_DIR.glob("SIM-*"):
        if path.is_file():
            path.unlink()


def main() -> None:
    clear_existing_simulated_files()

    for school in SCHOOLS:
        build_transcript_docx(OUTPUT_DIR / school["filename"], school)

    build_internship_certificate_docx(OUTPUT_DIR / INTERNSHIP_A["filename"], INTERNSHIP_A)
    build_recommendation_letter_docx(
        OUTPUT_DIR / "SIM-Amazon-Web-Services-Recommendation-Letter.docx",
        INTERNSHIP_A,
    )
    build_internship_certificate_docx(OUTPUT_DIR / INTERNSHIP_B["filename"], INTERNSHIP_B)
    build_resume_docx(OUTPUT_DIR / "SIM-Complete-Resume.docx")


if __name__ == "__main__":
    main()
