from google_auth import get_credentials
from google_forms import create_google_form
from models import ParsedTest, Question


def main():
    test = ParsedTest(
        title="Test Form Created From Python",
        questions=[
            Question(
                text="Что измеряется в амперах?",
                options=[
                    "Напряжение",
                    "Сила тока",
                    "Сопротивление",
                    "Мощность",
                ],
                correct_answer="Сила тока",
            ),
            Question(
                text="Единица измерения напряжения?",
                options=[
                    "Вольт",
                    "Ом",
                    "Ампер",
                    "Джоуль",
                ],
                correct_answer="Вольт",
            ),
        ],
    )

    creds = get_credentials()
    form_info = create_google_form(test, creds)

    print("Google Form created.")
    print("Form ID:", form_info["form_id"])
    print("Responder URL:", form_info["responder_url"])
    print("Edit URL:", form_info["edit_url"])


if __name__ == "__main__":
    main()