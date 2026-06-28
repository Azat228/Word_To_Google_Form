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
    for path in paths:
        if Path(path).exists():
            return path

    return None


def register_fonts() -> tuple[str, str]:
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
    if text is None:
        text = ""

    safe_text = str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return Paragraph(safe_text, style)


def get_category_counts(graded_results: list[dict[str, Any]]) -> Counter:
    counter = Counter()

    for result in graded_results:
        label = result.get("grade_label", "Без категории")
        counter[label] += 1

    return counter


def export_summary_pdf(
    graded_results: list[dict[str, Any]],
    output_path: str,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    regular_font, bold_font = register_fonts()

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

    doc = SimpleDocTemplate(
        str(output),
        pagesize=landscape(A4),
        rightMargin=1.2 * cm,
        leftMargin=1.2 * cm,
        topMargin=1.2 * cm,
        bottomMargin=1.2 * cm,
    )

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

    story.append(Spacer(1, 8))

    total_students = len(graded_results)

    story.append(
        paragraph(f"Количество ответов: {total_students}", normal_style)
    )

    story.append(Spacer(1, 8))

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

    has_high_risk = any(
        result.get("risk_flag") in ("Высокий риск", "риск") for result in graded_results
    )

    risk_header_style = risk_style if has_high_risk else header_style

    main_table_data = [
        [
            paragraph("№", header_style),
            paragraph("ФИО", header_style),
            paragraph("Класс", header_style),
            paragraph("Балл", header_style),
            paragraph("Макс.", header_style),
            paragraph("Градация", header_style),
            paragraph("Высокий риск", risk_header_style),
        ]
    ]

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

    story.append(main_table)

    doc.build(story)

    return str(output)