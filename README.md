# Word to Google Form

A desktop Python application that converts Word-based questionnaires into Google Forms, downloads responses, grades them with a saved answer key, and exports Excel reports.

## Key features

- Create Google Forms from structured Word documents
- Support for two workflows:
  - Four-option tests with scored answer choices
  - Yes/No keyed questionnaires with custom scoring keys
- Save and reuse answer keys for grading
- Download and normalize Google Form responses
- Generate Excel summary and detailed reports
- Create QR codes for form links

## Getting started

### 1. Install dependencies

From the project root:

```bash
python -m pip install -r requirements.txt
```

### 2. Configure Google API access

1. Create a Google Cloud project.
2. Enable the Google Forms API.
3. Create OAuth 2.0 client credentials.
4. Download `credentials.json` and place it in the project root.
5. Run the app once to complete OAuth and generate `token.json`.

### 3. Run the application

```bash
python main.py
```

The app launches a simple desktop menu where you choose between:

- `4 варианта ответа` — four-option scoring tests
- `ДА / НЕТ с ключом` — yes/no keyed questionnaires

## Workflows

### Four-option workflow
Use this mode for questionnaires where each question has four answer options and each option can be assigned a score. The app parses the Word document, creates the corresponding Google Form, and saves an answer key for later grading.

### Yes/No keyed workflow
Use this mode for questionnaires where scoring depends on yes/no response patterns. Enter question numbers for `YES = 1 point` and `NO = 1 point` in the UI to define the scoring key.

## Word document format

The parser expects a structured Word document containing:

- Optional title or introduction text
- Numbered questions like `1. Question text`
- Answer options immediately following each question

For four-option tests, each question should be followed by four answer options.
For yes/no keyed questionnaires, the same question structure is used and scoring is controlled through the answer key fields in the app.

## What the app does

## How the app works

### 1. Start the application
Run the app from the project root:

```bash
python main.py
```

You will see a start window with two options:

- Four answer options
- Yes/No keyed questionnaire

![Main menu with test type selection](img_for_readme/main_menu.png)

### 2. Choose a test type
The app offers two modes:

1. Four-option mode
   - Best for tests where each question has four answer choices.
   - The user can assign numeric scores to each option.
   - Thresholds can be configured to label the final score range.
   
![Four-option test configuration screen](img_for_readme/4_variant.png)
2. Yes/No keyed mode
   - Best for questionnaires such as the Beck Hopelessness Scale.
   - The user specifies which question numbers count as one point for "Yes" and which count as one point for "No".
   - Thresholds can be configured to classify the final result.

![Yes/No keyed questionnaire screen](img_for_readme/yes_no_key.png)

### 3. Import a Word document
The app opens a Word file using the Tkinter file picker. The parser reads the document and extracts:

- the test title,
- numbered questions,
- answer options,
- scoring information or key definitions.

### 4. Create a Google Form
After the file is parsed, the app authenticates with Google and creates a Google Form. The generated form includes:



- a student or respondent identifier field,
- the parsed questions,
- the answer choices defined in the Word file.

The app also saves an answer key JSON file for later grading.

### 5. Share the form and collect responses
Once the form is created, the responder link can be shared. The app can also generate a QR code for that link.

### 6. Download responses and generate reports
When responses are available, the user enters the Google Form ID and launches the report workflow. The app:

- authenticates with Google again,
- downloads the form responses,
- normalizes the response data,
- grades them against the saved answer key,
- creates Excel reports in a selected folder.

## Output files

The app may create:

- `answer_key_<form_id>.json` — saved answer key
- `responses_normalized.json` — normalized response data
- `graded_results.json` — graded responses
- `report.xlsx` — summary Excel report
- `detailed_report.xlsx` — detailed Excel report
- `qr_code_<form_id>.png` — QR code for the form link

## Project structure

- `main.py` — application entry point
- `requirements.txt` — Python dependencies
- `credentials.json` / `token.json` — Google OAuth files
- `school_form_app/ui/` — Tkinter desktop UI modules
- `school_form_app/parsing/` — Word parsing logic
- `school_form_app/google_api/` — Google Forms authentication and API integration
- `school_form_app/reports/` — grading, export, and report generation
- `school_form_app/models.py` — shared data models

## Notes

- Keep `credentials.json` and `token.json` private.
- If parsing fails, check that the Word file uses numbered questions and consistent answer option formatting.
- The desktop UI is in Russian and supports both scored and keyed questionnaire workflows.
