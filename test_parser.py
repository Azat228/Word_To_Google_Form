from parser_docx import parse_docx


def main():
    parsed_test = parse_docx(
        "БЕК депрессия BDI_подростки_школа.docx",
        option_scores=[0, 1, 2, 3],
    )

    print("Title:", parsed_test.title)
    print("Questions found:", len(parsed_test.questions))
    print()

    for question in parsed_test.questions:
        print(f"{question.number}. {question.title}")

        for option in question.options:
            print(f"   - [{option.score}] {option.text}")

        print()


if __name__ == "__main__":
    main()