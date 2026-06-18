import re
from docx import Document
from models import ParsedTest, Question


QUESTION_RE = re.compile(r"^\s*(\d+)[\.\)]\s*(.+)")
OPTION_RE = re.compile(r"^\s*([A-DА-Г])[\.\)]\s*(.+)", re.IGNORECASE)
TITLE_RE = re.compile(r"^\s*Название\s*:\s*(.+)", re.IGNORECASE)


def clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def parse_docx(path: str) -> ParsedTest:
    document = Document(path)

    lines = []
    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)
        if text:
            lines.append(text)

    title = "Untitled test"
    questions = []

    current_question_text = None
    current_options = []
    current_correct = None

    def save_current_question():
        nonlocal current_question_text, current_options, current_correct

        if current_question_text is None:
            return

        if len(current_options) < 2:
            raise ValueError(
                f"Question has less than 2 options: {current_question_text}"
            )

        question = Question(
            text=current_question_text,
            options=current_options,
            correct_answer=current_correct,
        )

        questions.append(question)

        current_question_text = None
        current_options = []
        current_correct = None

    for line in lines:
        title_match = TITLE_RE.match(line)
        if title_match:
            title = title_match.group(1).strip()
            continue

        question_match = QUESTION_RE.match(line)
        if question_match:
            save_current_question()
            current_question_text = question_match.group(2).strip()
            continue

        option_match = OPTION_RE.match(line)
        if option_match:
            if current_question_text is None:
                raise ValueError(f"Option found before question: {line}")

            option_text = option_match.group(2).strip()

            is_correct = "*" in option_text
            option_text = option_text.replace("*", "").strip()

            current_options.append(option_text)

            if is_correct:
                current_correct = option_text

            continue

        if current_question_text is not None and not current_options:
            current_question_text += " " + line

    save_current_question()

    if not questions:
        raise ValueError("No questions found. Check the Word format.")

    return ParsedTest(
        title=title,
        questions=questions,
    )