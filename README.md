# Word_to_Google_Form

A small toolset to convert tests in Microsoft Word (.docx) into Google Forms, collect responses, grade them and export Excel reports.

**Key features**

- Parse .docx test documents and extract questions and options.
- Create a Google Form from the parsed test.
- Save an answer key (JSON) for grading.
- Download and normalize Google Form responses.
- Grade responses, generate summary and detailed results.
- Export Excel reports (short and detailed) using `openpyxl`.

**Important files**

- [main.py](main.py#L1) — CLI tool to parse a .docx and create a Google Form.
- [app.py](app.py#L1) — Tkinter GUI application for selecting a .docx, creating a form and exporting reports.
- [parser_docx.py](parser_docx.py#L1) — .docx parsing logic.
- [google_auth.py](google_auth.py#L1) — Google OAuth helper (requires `credentials.json`).
- [google_forms.py](google_forms.py#L1) — Functions to create Google Forms.
- [answer_key.py](answer_key.py#L1) — Save/load answer key JSON.
- [google_responses.py](google_responses.py#L1) — Download & normalize form responses.
- [grading.py](grading.py#L1) — Grade responses and helper to save JSON results.
- [excel_export.py](excel_export.py#L1) — Export reports to Excel files.
- [models.py](models.py#L1) — Data models used across the project.
- `credentials.json` / `token.json` — Google API credentials and token (not checked into VCS).
- Tests: `test_*.py` files for unit tests.

## Requirements

Install runtime dependencies:

```
python -m pip install -r requirements.txt
```

See [requirements.txt](requirements.txt#L1) for pinned versions.

## Google API setup

1. Go to the Google Cloud Console and create a project.
2. Enable the Google Forms API and Google Drive API (if required).
3. Create OAuth 2.0 Client credentials and download the `credentials.json` file.
4. Place `credentials.json` in the project root.
5. On first run the app will open a browser to get consent and will save `token.json`.

## Usage

CLI (create a form from a .docx):

```
python main.py "path/to/test.docx"
```

GUI (interactive):

```
python app.py
```

- In the GUI you can choose a Word file, create the Google Form, then fetch responses and export Excel reports.
- The GUI uses the same Google credentials flow; ensure `credentials.json` is present.

## Outputs

- Answer keys: `answer_key.json` or `answer_key_<form_id>.json`
- Normalized responses: `responses_normalized.json`
- Graded results: `graded_results.json`
- Excel reports: created in the directory you select via the GUI (short and detailed reports).



## Notes & Troubleshooting

- Keep `credentials.json` private; do not commit it to source control.
- If Google API calls fail, check that the OAuth consent and scopes are configured correctly for the Forms API.
- If parsing fails for a specific .docx, open it in Word and verify the test formatting matches the expected patterns in `parser_docx.py`.