# Word to Google Form

A Python application that converts multiple-choice tests from Microsoft Word (`.docx`) into Google Forms, downloads responses, grades them, and exports Excel reports.

## What this project does

- Parses a `.docx` test file and extracts numbered questions with four answer options.
- Creates a Google Form with student fields and parsed test questions.
- Saves an answer key as JSON for grading.
- Downloads and normalizes Google Form responses.
- Grades responses by matching answers to the saved answer key.
- Generates summary and detailed Excel reports.
- Creates a QR code for the Google Form responder link.

## Project structure

- `main.py` — application entry point.
- `requirements.txt` — Python dependency list.
- `credentials.json` / `token.json` — Google OAuth credentials and saved token.

### Core package files

- `school_form_app/ui/desktop_app.py` — Tkinter GUI interface.
- `school_form_app/parsing/docx_parser.py` — parses `.docx` files and builds the in-memory test structure.
- `school_form_app/google_api/auth.py` — Google OAuth credential flow.
- `school_form_app/google_api/forms.py` — creates Google Forms programmatically.
- `school_form_app/google_api/responses.py` — downloads and normalizes form responses.
- `school_form_app/reports/answer_key.py` — saves answer key JSON.
- `school_form_app/reports/grading.py` — grades student responses.
- `school_form_app/reports/excel_export.py` — exports Excel reports.
- `school_form_app/reports/qr_code.py` — generates QR codes for form URLs.
- `school_form_app/models.py` — dataclasses for tests, questions, options, and thresholds.

## Requirements

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Required packages:

- `python-docx`
- `google-api-python-client`
- `google-auth-oauthlib`
- `google-auth`
- `openpyxl`
- `qrcode[pil]`

## Google API setup

1. Create a Google Cloud project.
2. Enable the Google Forms API.
3. Create OAuth 2.0 client credentials.
4. Download `credentials.json` and place it in the project root.
5. Run the app to complete authorization and generate `token.json`.

## Usage

Run the app:

```bash
python main.py
```

### GUI workflow

1. Select a Word `.docx` file.
2. Adjust answer option scores and grading thresholds if needed.
3. Click `Создать Google Form` to create the form and save the answer key.
4. Optionally download a QR code for the form link.
5. Click `Получить ответы и создать Excel` to fetch responses and export reports.

## Input format expectations

- Questions must use numbered headings like `1. Question text`.
- Each question should be followed by exactly four answer option lines.
- Instructions may appear before the first numbered question.
- The parser stops at a line beginning with `подсчет результатов`.

## Output files

- `answer_key_<form_id>.json` — saved answer key.
- `responses_normalized.json` — normalized Google Forms responses.
- `graded_results.json` — graded response results.
- Excel reports in the selected output folder:
  - `report.xlsx` — summary report.
  - `detailed_report.xlsx` — detailed report.
- `qr_code_<form_id>.png` — QR code for the form responder link.

## Notes & Troubleshooting

- Keep `credentials.json` private and do not commit it.
- If parsing fails, ensure the `.docx` uses the expected question/option formatting.
- The GUI supports custom grading thresholds.
