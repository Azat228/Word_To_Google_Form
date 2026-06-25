from school_form_app.reports.grading import grade_responses, save_json


def main():
    answer_key_path = input("Paste answer key file name: ").strip()

    if not answer_key_path:
        print("Answer key file name is empty.")
        return

    graded_results = grade_responses(
        responses_path="responses_normalized.json",
        answer_key_path=answer_key_path,
    )

    save_json(graded_results, "graded_results.json")

    print(f"Graded responses: {len(graded_results)}")
    print("Saved to graded_results.json")

    if graded_results:
        first = graded_results[0]

        print()
        print("First graded response:")
        print("Name:", first["student_name"])
        print("Class:", first["student_class"])
        print("Email:", first["student_email"])
        print("Total score:", first["total_score"], "/", first["max_score"])
        print("Grade:", first["grade_label"])

        print()
        print("Question details:")

        for question in first["questions"]:
            print(
                f'{question["number"]}. {question["title"]}: '
                f'{question["answer"]} '
                f'[{question["score"]}/{question["max_score"]}]'
            )


if __name__ == "__main__":
    main()