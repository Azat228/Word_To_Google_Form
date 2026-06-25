import re
from docx import Document

from school_form_app.models import ParsedTest, Question, AnswerOption


QUESTION_RE = re.compile(r"^\s*(\d+)[\.\)]\s*(.+)")


def clean_text(text: str) -> str:
    return " ".join(text.strip().split())


def get_paragraph_lines(document: Document) -> list[str]:
    lines = []

    for paragraph in document.paragraphs:
        raw_text = paragraph.text

        for part in raw_text.splitlines():
            text = clean_text(part)

            if text:
                lines.append(text)

    return lines


def extract_title(lines: list[str]) -> str:
    for line in lines:
        if line:
            return line

    return "Untitled test"


def extract_instructions(lines: list[str]) -> str | None:
    instruction_lines = []
    inside_instruction = False

    for line in lines:
        if QUESTION_RE.match(line):
            break

        if line.lower().startswith("инструкция"):
            inside_instruction = True

        if inside_instruction:
            instruction_lines.append(line)

    if not instruction_lines:
        return None

    return "\n".join(instruction_lines)


def parse_four_option_questions(
    lines: list[str],
    option_scores: list[int],
) -> list[Question]:
    if len(option_scores) != 4:
        raise ValueError("option_scores must contain exactly 4 numbers.")

    questions = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if line.lower().startswith("подсчет результатов"):
            break

        match = QUESTION_RE.match(line)

        if not match:
            index += 1
            continue

        question_number = int(match.group(1))
        question_title = match.group(2).strip()

        option_texts = []
        index += 1

        while index < len(lines) and len(option_texts) < 4:
            next_line = lines[index]

            if next_line.lower().startswith("подсчет результатов"):
                break

            if QUESTION_RE.match(next_line):
                raise ValueError(
                    f"Question {question_number} has less than 4 options."
                )

            option_texts.append(next_line)
            index += 1

        if len(option_texts) != 4:
            raise ValueError(
                f"Question {question_number} should have 4 options, "
                f"but found {len(option_texts)}."
            )

        options = [
            AnswerOption(text=option_texts[0], score=option_scores[0]),
            AnswerOption(text=option_texts[1], score=option_scores[1]),
            AnswerOption(text=option_texts[2], score=option_scores[2]),
            AnswerOption(text=option_texts[3], score=option_scores[3]),
        ]

        questions.append(
            Question(
                number=question_number,
                title=question_title,
                options=options,
            )
        )

    if not questions:
        raise ValueError("No 4-option questions found in the Word file.")

    return questions


def parse_docx(
    path: str,
    option_scores: list[int] | None = None,
) -> ParsedTest:
    if option_scores is None:
        option_scores = [0, 1, 2, 3]

    document = Document(path)
    lines = get_paragraph_lines(document)

    title = extract_title(lines)
    instructions = extract_instructions(lines)
    questions = parse_four_option_questions(lines, option_scores)

    return ParsedTest(
        title=title,
        instructions=instructions,
        questions=questions,
    )