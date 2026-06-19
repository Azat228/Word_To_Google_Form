import json

from models import ParsedTest


def save_answer_key(parsed_test: ParsedTest, path: str = "answer_key.json") -> None:
    data = {
        "title": parsed_test.title,
        "questions": [
            {
                "text": question.text,
                "options": question.options,
                "correct_answer": question.correct_answer,
            }
            for question in parsed_test.questions
        ],
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)