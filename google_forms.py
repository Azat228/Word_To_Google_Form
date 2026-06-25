from googleapiclient.discovery import build

from models import ParsedTest


def create_google_form(parsed_test: ParsedTest, creds) -> dict:
    service = build("forms", "v1", credentials=creds)

    created_form = service.forms().create(
        body={
            "info": {
                "title": parsed_test.title,
                "documentTitle": parsed_test.title,
            }
        }
    ).execute()

    form_id = created_form["formId"]

    requests = []

    # Optional description / instructions
    if parsed_test.instructions:
        requests.append(
            {
                "updateFormInfo": {
                    "info": {
                        "description": parsed_test.instructions
                    },
                    "updateMask": "description",
                }
            }
        )

    # Student full name
    requests.append(
        {
            "createItem": {
                "item": {
                    "title": "ФИО ученика",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            },
                        }
                    },
                },
                "location": {
                    "index": 0
                },
            }
        }
    )

    # Student class
    requests.append(
        {
            "createItem": {
                "item": {
                    "title": "Класс",
                    "questionItem": {
                        "question": {
                            "required": True,
                            "textQuestion": {
                                "paragraph": False
                            },
                        }
                    },
                },
                "location": {
                    "index": 1
                },
            }
        }
    )

    # Student email, optional
    requests.append(
        {
            "createItem": {
                "item": {
                    "title": "Email ученика",
                    "questionItem": {
                        "question": {
                            "required": False,
                            "textQuestion": {
                                "paragraph": False
                            },
                        }
                    },
                },
                "location": {
                    "index": 2
                },
            }
        }
    )

    for index, question in enumerate(parsed_test.questions, start=3):
        requests.append(
            {
                "createItem": {
                    "item": {
                        "title": f"{question.number}. {question.title}",
                        "questionItem": {
                            "question": {
                                "required": True,
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [
                                        {"value": option.text}
                                        for option in question.options
                                    ],
                                    "shuffle": False,
                                },
                            }
                        },
                    },
                    "location": {
                        "index": index
                    },
                }
            }
        )

    service.forms().batchUpdate(
        formId=form_id,
        body={
            "requests": requests
        },
    ).execute()

    return {
        "form_id": form_id,
        "responder_url": f"https://docs.google.com/forms/d/{form_id}/viewform",
        "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
    }