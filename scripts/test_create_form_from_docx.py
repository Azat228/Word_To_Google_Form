"""Smoke test for creating a Google Form from a Word document."""

from school_form_app.parsing.docx_parser import parse_docx
from school_form_app.google_api.auth import get_credentials
from school_form_app.google_api.forms import create_google_form
from school_form_app.reports.answer_key import save_answer_key
from school_form_app.models import GradeThreshold


def main():
    option_scores = [0, 1, 2, 3]

    thresholds = [
        GradeThreshold(0, 9, "Минимальный уровень"),
        GradeThreshold(10, 18, "Лёгкая степень"),
        GradeThreshold(19, 29, "Умеренная степень"),
        GradeThreshold(30, 63, "Выраженная степень"),
    ]

    parsed_test = parse_docx(
        "БЕК депрессия BDI_подростки_школа.docx",
        option_scores=option_scores,
    )

    parsed_test.thresholds = thresholds

    print("Title:", parsed_test.title)
    print("Questions found:", len(parsed_test.questions))

    creds = get_credentials()

    print("Creating Google Form...")
    form_info = create_google_form(parsed_test, creds)

    answer_key_path = f"answer_key_{form_info['form_id']}.json"

    save_answer_key(
        parsed_test,
        path=answer_key_path,
        option_scores=option_scores,
        thresholds=thresholds,
    )

    print()
    print("Google Form created.")
    print("Form ID:", form_info["form_id"])
    print("Responder URL:", form_info["responder_url"])
    print("Edit URL:", form_info["edit_url"])
    print("Answer key:", answer_key_path)


if __name__ == "__main__":
    main()