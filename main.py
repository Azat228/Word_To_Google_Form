import sys
from pathlib import Path

from parser_docx import parse_docx
from google_auth import get_credentials
from google_forms import create_google_form
from answer_key import save_answer_key


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "path/to/test.docx"')
        return

    docx_path = Path(sys.argv[1])

    if not docx_path.exists():
        print(f"File not found: {docx_path}")
        return

    print("Reading Word file...")
    parsed_test = parse_docx(str(docx_path))

    print()
    print(f"Title: {parsed_test.title}")
    print(f"Questions found: {len(parsed_test.questions)}")

    print()
    print("Preview:")

    for index, question in enumerate(parsed_test.questions, start=1):
        print(f"{index}. {question.text}")

        for option in question.options:
            if option == question.correct_answer:
                print(f"   - {option}  <-- correct")
            else:
                print(f"   - {option}")

        print()

    answer = input("Create Google Form? [y/N]: ").strip().lower()

    if answer != "y":
        print("Cancelled.")
        return

    print()
    print("Authorizing Google account...")
    creds = get_credentials()

    print("Creating Google Form...")
    form_info = create_google_form(parsed_test, creds)

    print("Saving answer key...")
    save_answer_key(parsed_test)

    print()
    print("Done.")
    print("Form ID:", form_info["form_id"])
    print("Responder URL:", form_info["responder_url"])
    print("Edit URL:", form_info["edit_url"])
    print()
    print("Answer key saved to answer_key.json")


if __name__ == "__main__":
    main()