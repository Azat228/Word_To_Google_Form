import json
from typing import Any

from googleapiclient.discovery import build


def get_forms_service(creds):
    return build("forms", "v1", credentials=creds)


def get_raw_form_responses(form_id: str, creds) -> list[dict]:
    service = get_forms_service(creds)

    all_responses = []
    page_token = None

    while True:
        request = service.forms().responses().list(
            formId=form_id,
            pageToken=page_token,
        )

        response = request.execute()

        all_responses.extend(response.get("responses", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return all_responses


def get_form_question_map(form_id: str, creds) -> dict[str, str]:
    """
    Returns:
    {
        "question_id_from_google": "Question title from Google Form"
    }
    """
    service = get_forms_service(creds)

    form = service.forms().get(formId=form_id).execute()

    question_map = {}

    for item in form.get("items", []):
        title = item.get("title", "")

        question_item = item.get("questionItem")
        if not question_item:
            continue

        question = question_item.get("question")
        if not question:
            continue

        question_id = question.get("questionId")
        if not question_id:
            continue

        question_map[question_id] = title

    return question_map


def extract_answer_value(answer_object: dict[str, Any]) -> str | list[str] | None:
    """
    Google Forms answer format usually looks like:

    {
        "questionId": "...",
        "textAnswers": {
            "answers": [
                {"value": "..."}
            ]
        }
    }

    For our current app, every answer should usually be one string.
    """
    text_answers = answer_object.get("textAnswers", {})
    answers = text_answers.get("answers", [])

    values = []

    for answer in answers:
        value = answer.get("value")

        if value is not None:
            values.append(value)

    if not values:
        return None

    if len(values) == 1:
        return values[0]

    return values


def normalize_form_responses(form_id: str, creds) -> list[dict]:
    """
    Converts Google raw responses into easier format:

    [
        {
            "response_id": "...",
            "submitted_at": "...",
            "answers": {
                "ФИО ученика": "Иван Иванов",
                "Класс": "9А",
                "1. Настроение": "Я не чувствую себя расстроенным"
            }
        }
    ]
    """
    raw_responses = get_raw_form_responses(form_id, creds)
    question_map = get_form_question_map(form_id, creds)

    normalized_responses = []

    for response in raw_responses:
        normalized = {
            "response_id": response.get("responseId"),
            "submitted_at": response.get("lastSubmittedTime") or response.get("createTime"),
            "answers": {},
        }

        raw_answers = response.get("answers", {})

        for question_id, answer_object in raw_answers.items():
            question_title = question_map.get(question_id, question_id)
            answer_value = extract_answer_value(answer_object)

            normalized["answers"][question_title] = answer_value

        normalized_responses.append(normalized)

    return normalized_responses


def save_json(data, path: str) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def save_raw_responses(
    responses: list[dict],
    path: str = "responses_raw.json",
) -> None:
    save_json(responses, path)


def save_normalized_responses(
    responses: list[dict],
    path: str = "responses_normalized.json",
) -> None:
    save_json(responses, path)