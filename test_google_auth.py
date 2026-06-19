from google_auth import get_credentials


def main():
    creds = get_credentials()

    if creds and creds.valid:
        print("Google authorization works.")
    else:
        print("Google authorization failed.")


if __name__ == "__main__":
    main()