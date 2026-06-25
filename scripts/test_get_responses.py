from google_auth import get_credentials
from google_responses import get_raw_form_responses, save_raw_responses


def main():
    form_id = input("Paste Google Form ID: ").strip()

    if not form_id:
        print("Form ID is empty.")
        return

    creds = get_credentials()

    print("Getting responses...")
    responses = get_raw_form_responses(form_id, creds)

    print(f"Responses found: {len(responses)}")

    save_raw_responses(responses)

    print("Saved to responses_raw.json")


if __name__ == "__main__":
    main()