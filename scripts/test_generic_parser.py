from school_form_app.config.template_loader import find_config_by_id
from school_form_app.parsing.generic_parser import parse_test_from_config


def print_preview(parsed_test):
    print("Title:", parsed_test.title)
    print("Questions:", len(parsed_test.questions))
    print("Thresholds:", len(parsed_test.thresholds))
    print()

    for question in parsed_test.questions[:5]:
        print(f"{question.number}. {question.title}")

        for option in question.options:
            print(f"   [{option.score}] {option.text}")

        print()


def main():
    config_id = input("Config ID: ").strip()
    docx_path = input("DOCX path: ").strip()

    config = find_config_by_id(config_id)

    if config is None:
        print(f"Config not found: {config_id}")
        return

    parsed_test = parse_test_from_config(
        docx_path=docx_path,
        config=config,
    )

    print_preview(parsed_test)


if __name__ == "__main__":
    main()