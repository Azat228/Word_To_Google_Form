from grading import load_json
from excel_export import export_reports


def main():
    graded_results = load_json("graded_results.json")

    report_path, detailed_report_path = export_reports(
        graded_results=graded_results,
        output_dir=".",
    )

    print("Excel reports created:")
    print(report_path)
    print(detailed_report_path)


if __name__ == "__main__":
    main()