import sys
from pathlib import Path

from parser_docx import parse_docx


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


if __name__ == "__main__":
    main()