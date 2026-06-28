import json
from typing import Any


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_grade_label(total_score: int, thresholds: list[dict]) -> str:
    for threshold in thresholds:
        min_score = threshold["min_score"]
        max_score = threshold["max_score"]
        label = threshold["label"]

        if min_score <= total_score <= max_score:
            return label

    return "Без категории"


def find_student_answer(
    answers: dict,
    question_number: int,
    question_title: str,
):
    expected_key = f"{question_number}. {question_title}"

    if expected_key in answers:
        return answers[expected_key]

    # fallback, если Google/форма немного изменила title
    prefix = f"{question_number}."

    for key, value in answers.items():
        if key.startswith(prefix):
            return value

    return None


def get_option_score(question: dict, student_answer: str | None) -> int:
    if student_answer is None:
        return 0

    for option in question["options"]:
        if option["text"] == student_answer:
            return option["score"]

    return 0
def get_risk_flag(grade_label: str) -> str:
    label_lower = grade_label.lower()

    urgent_words = [
        "тяж",
        "высок",
        "выраж",
        "severe",
        "high",
        "urgent",
    ]

    review_words = [
        "умерен",
        "moderate",
    ]

    if any(word in label_lower for word in urgent_words):
        return "Высокий риск"

    if any(word in label_lower for word in review_words):
        return "риск"
    return "Нет"

def grade_single_response(response: dict, answer_key: dict) -> dict:
    answers = response["answers"]

    student_name = (
        answers.get("ФИО ученика")
        or answers.get("ФИО")
        or answers.get("ученика")
        or ""
    )

    student_class = (
        answers.get("Класс")
        or answers.get("класс")
        or ""
    )

    student_email = (
        answers.get("Email ученика")
        or answers.get("Email")
        or ""
    )

    question_results = []
    total_score = 0
    max_score = 0

    for question in answer_key["questions"]:
        question_number = question["number"]
        question_title = question["title"]

        student_answer = find_student_answer(
            answers=answers,
            question_number=question_number,
            question_title=question_title,
        )

        score = get_option_score(question, student_answer)

        max_question_score = max(
            option["score"]
            for option in question["options"]
        )

        total_score += score
        max_score += max_question_score

        question_results.append(
            {
                "number": question_number,
                "title": question_title,
                "answer": student_answer,
                "score": score,
                "max_score": max_question_score,
            }
        )

    thresholds = answer_key.get("thresholds", [])
    grade_label = get_grade_label(total_score, thresholds)
    risk_flag = get_risk_flag(grade_label)
    return {
        "response_id": response.get("response_id"),
        "submitted_at": response.get("submitted_at"),
        "student_name": student_name,
        "student_class": student_class,
        "student_email": student_email,
        "total_score": total_score,
        "max_score": max_score,
        "grade_label": grade_label,
        "questions": question_results,
        "risk_flag": risk_flag,
    }


def grade_responses(
    responses_path: str,
    answer_key_path: str,
) -> list[dict]:
    responses = load_json(responses_path)
    answer_key = load_json(answer_key_path)

    graded_results = []

    for response in responses:
        graded = grade_single_response(response, answer_key)
        graded_results.append(graded)

    return graded_results