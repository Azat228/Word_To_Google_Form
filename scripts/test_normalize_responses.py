"""Smoke test for the response normalization workflow."""

from school_form_app.google_api.auth import get_credentials
from school_form_app.google_api.responses import (
    normalize_form_responses,
    save_normalized_responses,
)

def main():
    form_id = input("Paste Google Form ID: ").strip()

    if not form_id:
        print("Form ID is empty.")
        return

    creds = get_credentials()

    print("Getting and normalizing responses...")
    responses = normalize_form_responses(form_id, creds)

    print(f"Responses found: {len(responses)}")

    save_normalized_responses(responses)

    print("Saved to responses_normalized.json")

    if responses:
        print()
        print("First response preview:")

        first_response = responses[0]

        for question_title, answer in first_response["answers"].items():
            print(f"{question_title}: {answer}")


if __name__ == "__main__":
    main()