"""Generate a PDF summary report from graded test results.

This module converts the graded output from the reporting pipeline into a
presentation-friendly PDF document. It prepares the document layout, applies
consistent styling, builds summary tables for grade categories, and renders a
student-by-student results table that can be shared with teachers or parents.
"""

from pathlib import Path
from collections import Counter
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def find_existing_font(paths: list[str]) -> str | None:
    # ReportLab needs actual font files on disk before it can register them.
    # This helper checks a list of common Windows and Unix font locations and
    # returns the first one that exists so the PDF can use a local, readable
    # typeface instead of falling back to a generic font.
    for path in paths:
        if Path(path).exists():
            return path

    return None


def register_fonts() -> tuple[str, str]:
    # Register a regular and a bold font with ReportLab so the PDF can use a
    # familiar visual style. If system fonts are unavailable, the function
    # gracefully falls back to ReportLab's default fonts.
    regular_font_path = find_existing_font(
        [
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
    )

    bold_font_path = find_existing_font(
        [
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
    )

    if regular_font_path:
        pdfmetrics.registerFont(
            TTFont("AppFont", regular_font_path)
        )
        regular_font = "AppFont"
    else:
        regular_font = "Helvetica"

    if bold_font_path:
        pdfmetrics.registerFont(
            TTFont("AppFont-Bold", bold_font_path)
        )
        bold_font = "AppFont-Bold"
    else:
        bold_font = regular_font

    return regular_font, bold_font


def make_paragraph_style(
    name: str,
    font_name: str,
    font_size: int = 10,
    leading: int = 12,
    alignment: int | None = None,
    text_color=colors.black,
) -> ParagraphStyle:
    # Build a reusable ReportLab paragraph style for the PDF. These styles
    # control font size, line spacing, alignment, and text color so the report
    # looks consistent across title, subtitle, body, and table content.
    style = ParagraphStyle(
        name=name,
        fontName=font_name,
        fontSize=font_size,
        leading=leading,
        textColor=text_color,
    )

    if alignment is not None:
        style.alignment = alignment

    return style


def paragraph(text: Any, style: ParagraphStyle) -> Paragraph:
    # Wrap a value in a ReportLab Paragraph object while escaping characters
    # that would otherwise be interpreted as HTML-like markup. This keeps the
    # PDF text safe even when the input contains symbols such as '<' or '&'.
    if text is None:
        text = ""

    safe_text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return Paragraph(safe_text, style)


def get_category_counts(graded_results: list[dict[str, Any]]) -> Counter:
    # Count how many students fall into each grade category. This is used to
    # build the summary table that shows the distribution of results across the
    # thresholds configured in the grading workflow.
    counter = Counter()

    for result in graded_results:
        label = result.get("grade_label", "Без категории")
        counter[label] += 1

    return counter


def export_summary_pdf(
    graded_results: list[dict[str, Any]],
    output_path: str,
) -> str:
    # Build the complete PDF report from the graded results.
    # The workflow is split into clear stages:
    # 1. Prepare the output file and select fonts.
    # 2. Define paragraph styles for the title, subtitle, body text, and tables.
    # 3. Create the document object with landscape orientation and margins.
    # 4. Add a title, summary text, and a grade-category table.
    # 5. Add the main results table with student names, scores, labels, and risk.
    # 6. Render the PDF to disk.
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Register fonts before building any paragraphs or tables so the PDF can use
    # the same typeface consistently throughout the document.
    regular_font, bold_font = register_fonts()

    # Start from ReportLab's built-in style templates and then override them with
    # the custom font names and spacing needed by this report.
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="TitleCustom",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=12,
    )

    subtitle_style = ParagraphStyle(
        name="SubtitleCustom",
        parent=styles["Normal"],
        fontName=regular_font,
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=10,
    )

    normal_style = make_paragraph_style(
        name="NormalCustom",
        font_name=regular_font,
        font_size=9,
        leading=11,
    )

    small_style = make_paragraph_style(
        name="SmallCustom",
        font_name=regular_font,
        font_size=8,
        leading=10,
    )

    header_style = make_paragraph_style(
        name="HeaderCustom",
        font_name=bold_font,
        font_size=9,
        leading=11,
        alignment=TA_CENTER,
        text_color=colors.white,
    )
    risk_style = make_paragraph_style(
        name="RiskCustom",
        font_name=bold_font,
        font_size=9,
        leading=11,
        alignment=TA_CENTER,
        text_color=colors.red,
    )   

    # Create the PDF document object with landscape layout so the student table
    # fits comfortably on one page or a small number of pages.
    doc = SimpleDocTemplate(
        str(output),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

    # The ReportLab story is a list of building blocks that will be rendered in
    # order. Each element can be a paragraph, spacer, or table.
    story = []

    story.append(
        Paragraph("Краткий отчёт по результатам тестирования", title_style)
    )

    story.append(
        Paragraph(
            "Автоматический подсчёт результатов. "
            "Отчёт не является диагнозом. "
            "При высоких показателях требуется проверка специалистом.",
            subtitle_style,
        )
    )

    # Add spacing between major sections so the PDF is visually readable.
    story.append(Spacer(1, 8))

    total_students = len(graded_results)

    story.append(
        paragraph(f"Количество ответов: {total_students}", normal_style)
    )

    story.append(Spacer(1, 8))

    # Summarize how many students fell into each grade category before listing
    # every individual result in the detailed table.
    category_counts = get_category_counts(graded_results)

    if category_counts:
        category_table_data = [
            [
                paragraph("Градация", header_style),
                paragraph("Количество", header_style),
            ]
        ]

        for label, count in category_counts.items():
            category_table_data.append(
                [
                    paragraph(label, normal_style),
                    paragraph(count, normal_style),
                ]
            )

        category_table = Table(
            category_table_data,
            colWidths=[12 * cm, 4 * cm],
        )

        category_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ]
            )
        )

        story.append(category_table)
        story.append(Spacer(1, 14))

    # Prepare the main table header. Each column corresponds to a meaningful
    # part of the student result: number, name, class, score, max score,
    # grade label, and risk indicator.
    main_table_data = [
        [
            paragraph("№", header_style),
            paragraph("ФИО", header_style),
            paragraph("Класс", header_style),
            paragraph("Балл", header_style),
            paragraph("Макс.", header_style),
            paragraph("Градация", header_style),
            paragraph("Высокий риск", header_style),
        ]
    ]

    # Fill the main table row by row so each student appears with their total
    # score, the final category, and the risk flag generated during grading.
    for index, result in enumerate(graded_results, start=1):
        main_table_data.append(
            [
                paragraph(index, normal_style),
                paragraph(result.get("student_name", ""), normal_style),
                paragraph(result.get("student_class", ""), normal_style),
                paragraph(result.get("total_score", 0), normal_style),
                paragraph(result.get("max_score", 0), normal_style),
                paragraph(result.get("grade_label", ""), small_style),
                paragraph(result.get("risk_flag", "Нет"), small_style),
            ]
        )

    # Create the main results table and define column widths so the content fits
    # well on landscape A4 pages without wrapping awkwardly.
    main_table = Table(
        main_table_data,
        colWidths=[
            1.2 * cm,
            6 * cm,
            2.2 * cm,
            1.8 * cm,
            1.8 * cm,
            8 * cm,
            4 * cm,
        ],
        repeatRows=1,
    )

    main_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (4, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
            ]
        )
    )

    # Apply the risk color only to the risk cell in rows that are flagged as
    # high risk or moderate risk. The rest of the row keeps the normal table style.
    for row_index, result in enumerate(graded_results, start=2):
        if result.get("risk_flag") in ("Высокий риск", "риск"):
            main_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (6, row_index), (6, row_index), colors.HexColor("#FFE6E6")),
                        ("TEXTCOLOR", (6, row_index), (6, row_index), colors.HexColor("#8B0000")),
                    ]
                )
            )

    # Append the finished results table to the story and build the PDF file.
    story.append(main_table)

    doc.build(story)

    return str(output)