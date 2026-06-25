import json
from school_form_app.models import ParsedTest, GradeThreshold


def save_answer_key(
    parsed_test: ParsedTest,
    path: str = "answer_key.json",
    option_scores: list[int] | None = None,
    thresholds: list[GradeThreshold] | None = None,
) -> None:
    data = {
        "title": parsed_test.title,
        "instructions": parsed_test.instructions,
        "option_scores": option_scores,
        "thresholds": [
            {
                "min_score": threshold.min_score,
                "max_score": threshold.max_score,
                "label": threshold.label,
            }
            for threshold in (thresholds or parsed_test.thresholds)
        ],
        "questions": [
            {
                "number": question.number,
                "title": question.title,
                "options": [
                    {
                        "text": option.text,
                        "score": option.score,
                    }
                    for option in question.options
                ],
            }
            for question in parsed_test.questions
        ],
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)