"""
Generic UI for creating Google Forms from test templates.

This window is the new replacement for separate test windows.

Old approach:
    - one window for BDI
    - one window for BHS
    - one window for Ferguson
    - one window for Burnout

New approach:
    - one generic window
    - user chooses a JSON test template
    - app chooses the correct parser automatically
"""

from dbm import error
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from school_form_app.config.template_loader import load_test_configs
from school_form_app.parsing.generic_parser import parse_test_from_config

from school_form_app.google_api.auth import get_credentials
from school_form_app.google_api.forms import create_google_form

from school_form_app.reports.answer_key import save_answer_key
from school_form_app.reports.qr_export import create_qr_code, get_qr_code_output_path
from school_form_app.google_api.responses import normalize_form_responses, save_normalized_responses

from school_form_app.reports.grading import grade_responses, save_json
from school_form_app.reports.excel_export import export_reports
from school_form_app.reports.pdf_export import export_summary_pdf
from school_form_app.reports.cleanup import cleanup_generated_files
class GenericTestApp:
    """
    Main generic test UI.

    This class does not care whether the test is:
        - BDI
        - BHS
        - Ferguson
        - Burnout

    It only cares about:
        - selected config
        - selected Word file
        - parsed_test result
    """

    def __init__(self, root):
        self.root = root

        # This will store all loaded JSON configs.
        self.test_configs = load_test_configs()

        # This will store the currently selected config dictionary.
        self.selected_config = None

        # This will store the selected Word file path.
        self.docx_path = None

        # This will store ParsedTest after preview/parsing.
        self.parsed_test = None

        # This will store created Google Form info.
        self.form_info = None

        # This will store path to saved answer key.
        self.answer_key_path = None

        self.build_ui()

    def build_ui(self):
        """
        Build the visible interface.
        """

        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        title_label = ttk.Label(
            main_frame,
            text="Generic Test App",
            font=("Arial", 16, "bold"),
        )
        title_label.pack(anchor="w", pady=(0, 10))

        # ------------------------------------------------------------
        # Template selection section
        # ------------------------------------------------------------

        template_frame = ttk.LabelFrame(
            main_frame,
            text="1. Test template",
            padding=10,
        )
        template_frame.pack(fill="x", pady=5)

        ttk.Label(
            template_frame,
            text="Choose test template:",
        ).grid(row=0, column=0, sticky="w")

        self.template_var = tk.StringVar()

        self.template_combobox = ttk.Combobox(
            template_frame,
            textvariable=self.template_var,
            state="readonly",
            width=60,
        )

        self.template_combobox["values"] = [
            config.get("name", config.get("id", "Unnamed test"))
            for config in self.test_configs
        ]

        self.template_combobox.grid(
            row=0,
            column=1,
            padx=10,
            sticky="we",
        )

        self.template_combobox.bind(
            "<<ComboboxSelected>>",
            self.on_template_selected,
        )

        template_frame.columnconfigure(1, weight=1)

        # ------------------------------------------------------------
        # Word file selection section
        # ------------------------------------------------------------

        file_frame = ttk.LabelFrame(
            main_frame,
            text="2. Word file",
            padding=10,
        )
        file_frame.pack(fill="x", pady=5)

        self.file_label_var = tk.StringVar(
            value="No Word file selected."
        )

        ttk.Button(
            file_frame,
            text="Choose Word file",
            command=self.choose_word_file,
        ).grid(row=0, column=0, sticky="w")

        ttk.Label(
            file_frame,
            textvariable=self.file_label_var,
        ).grid(row=0, column=1, padx=10, sticky="w")

        file_frame.columnconfigure(1, weight=1)

        # ------------------------------------------------------------
        # Action buttons
        # ------------------------------------------------------------

        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill="x", pady=10)

        ttk.Button(
            action_frame,
            text="Preview parsed test",
            command=self.preview_test,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            action_frame,
            text="Create Google Form",
            command=self.create_form,
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            action_frame,
            text="Save QR code",
            command=self.save_qr_code,
        ).pack(side="left")
                # ------------------------------------------------------------
        # Reports section
        # ------------------------------------------------------------

        reports_frame = ttk.LabelFrame(
            main_frame,
            text="3. Reports",
            padding=10,
        )
        reports_frame.pack(fill="x", pady=5)

        ttk.Label(
            reports_frame,
            text="Google Form ID:",
        ).grid(row=0, column=0, sticky="w")

        self.form_id_var = tk.StringVar()

        self.form_id_entry = ttk.Entry(
            reports_frame,
            textvariable=self.form_id_var,
            width=70,
        )
        self.form_id_entry.grid(
            row=0,
            column=1,
            padx=10,
            sticky="we",
        )

        ttk.Label(
            reports_frame,
            text="Answer key:",
        ).grid(row=1, column=0, sticky="w", pady=(8, 0))

        self.answer_key_var = tk.StringVar()

        self.answer_key_entry = ttk.Entry(
            reports_frame,
            textvariable=self.answer_key_var,
            width=70,
        )
        self.answer_key_entry.grid(
            row=1,
            column=1,
            padx=10,
            sticky="we",
            pady=(8, 0),
        )

        ttk.Button(
            reports_frame,
            text="Choose answer key",
            command=self.choose_answer_key,
        ).grid(row=1, column=2, sticky="w", pady=(8, 0))

        ttk.Label(
            reports_frame,
            text="Output folder:",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        self.output_dir_var = tk.StringVar(
            value="reports_output"
        )

        self.output_dir_entry = ttk.Entry(
            reports_frame,
            textvariable=self.output_dir_var,
            width=70,
        )
        self.output_dir_entry.grid(
            row=2,
            column=1,
            padx=10,
            sticky="we",
            pady=(8, 0),
        )

        ttk.Button(
            reports_frame,
            text="Choose folder",
            command=self.choose_output_folder,
        ).grid(row=2, column=2, sticky="w", pady=(8, 0))

        ttk.Button(
            reports_frame,
            text="Get responses and create Excel/PDF",
            command=self.create_reports,
        ).grid(row=3, column=1, sticky="w", padx=10, pady=(12, 0))

        reports_frame.columnconfigure(1, weight=1)
        # ------------------------------------------------------------
        # Output/log section
        # ------------------------------------------------------------

        log_frame = ttk.LabelFrame(
            main_frame,
            text="Log",
            padding=10,
        )
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(
            log_frame,
            height=22,
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)

        self.log("Generic Test App loaded.")

        if not self.test_configs:
            self.log("WARNING: No test configs found.")
        else:
            self.log(f"Loaded test configs: {len(self.test_configs)}")

    def log(self, message: str):
        """
        Add a message to the log box.
        """

        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def on_template_selected(self, event=None):
        """
        Called when user chooses a test template from dropdown.
        """

        selected_name = self.template_var.get()

        self.selected_config = None

        for config in self.test_configs:
            config_name = config.get(
                "name",
                config.get("id", "Unnamed test"),
            )

            if config_name == selected_name:
                self.selected_config = config
                break

        if self.selected_config is None:
            self.log(f"Template not found: {selected_name}")
            return

        self.parsed_test = None
        self.form_info = None
        self.answer_key_path = None

        self.log("")
        self.log(f"Selected template: {selected_name}")
        self.log(f"Config ID: {self.selected_config.get('id')}")
        self.log(f"Parser type: {self.selected_config.get('parser_type')}")

    def choose_word_file(self):
        """
        Open file picker and let user choose a .docx file.
        """

        file_path = filedialog.askopenfilename(
            title="Choose Word test file",
            filetypes=[
                ("Word files", "*.docx"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        self.docx_path = file_path
        self.parsed_test = None
        self.form_info = None
        self.answer_key_path = None

        self.file_label_var.set(file_path)

        self.log("")
        self.log(f"Selected Word file: {file_path}")

    def validate_template_and_file(self) -> bool:
        """
        Check that user selected both:
            - test template
            - Word file
        """

        if self.selected_config is None:
            messagebox.showwarning(
                "No template",
                "Please choose a test template first.",
            )
            return False

        if not self.docx_path:
            messagebox.showwarning(
                "No Word file",
                "Please choose a Word file first.",
            )
            return False

        if not Path(self.docx_path).exists():
            messagebox.showerror(
                "File not found",
                f"Word file does not exist:\n{self.docx_path}",
            )
            return False

        return True

    def parse_current_test(self):
        """
        Parse selected Word file using selected JSON config.

        The important line is:

            parse_test_from_config(...)

        That function decides which real parser to use.
        """

        if not self.validate_template_and_file():
            return None

        self.log("")
        self.log("Parsing Word file...")

        parsed_test = parse_test_from_config(
            docx_path=self.docx_path,
            config=self.selected_config,
        )

        self.parsed_test = parsed_test

        self.log(f"Parsed title: {parsed_test.title}")
        self.log(f"Questions found: {len(parsed_test.questions)}")
        self.log(f"Thresholds found: {len(parsed_test.thresholds)}")

        return parsed_test

    def preview_test(self):
        """
        Show parsed test preview in the log.
        """

        try:
            parsed_test = self.parse_current_test()

            if parsed_test is None:
                return

            self.log("")
            self.log("Preview:")
            self.log("-" * 50)

            for question in parsed_test.questions[:10]:
                self.log(f"{question.number}. {question.title}")

                for option in question.options:
                    self.log(f"   [{option.score}] {option.text}")

                self.log("")

            if len(parsed_test.questions) > 10:
                self.log(
                    f"...and {len(parsed_test.questions) - 10} more questions."
                )

        except Exception as error:
            messagebox.showerror(
                "Parsing error",
                str(error),
            )
            self.log(f"ERROR: {error}")

    def get_answer_key_output_path(self, form_id: str) -> Path:
        """
        Build answer key path.

        We keep answer keys in a separate folder:

            answer_keys/
                answer_key_<form_id>.json
        """

        answer_keys_dir = Path("answer_keys")
        answer_keys_dir.mkdir(exist_ok=True)

        return answer_keys_dir / f"answer_key_{form_id}.json"
    def save_qr_code(self):
        

    # """
    # Save QR code for the current Google Form.

    # This function uses self.form_info, which is created after pressing
    # "Create Google Form".

    # If the form has not been created yet, there is no responder_url,
    # so we show a warning.
    # """

        if not self.form_info:
            messagebox.showwarning(
            "No Google Form",
            "Create a Google Form first.",
            )
            return

        form_id = self.form_info.get("form_id")
        responder_url = self.form_info.get("responder_url")

        if not form_id or not responder_url:
            messagebox.showerror(
                "Missing form data",
                "Form ID or responder URL is missing.",
            )
            return

        try:
            qr_path = get_qr_code_output_path(form_id)

            saved_path = create_qr_code(
                url=responder_url,
                output_path=str(qr_path),
            )

            self.log("")
            self.log(f"QR code saved: {saved_path}")

            messagebox.showinfo(
                "QR code saved",
                f"QR code saved:\n{saved_path}",
            )

        except Exception as error:
            messagebox.showerror(
                "QR code error",
                str(error),
            )
            self.log(f"ERROR: {error}")
    def confirm_privacy_warning(self) -> bool:
        # """
        # Show privacy warning before creating reports.

        # Reports contain personal and sensitive student data.
        # The user should confirm before generating files.
        # """

        message = (
                "Warning: reports may contain personal and sensitive data:\n\n"
                "- student name\n"
                "- class\n"
                "- email\n"
                "- psychological test answers\n"
                "- total scores and categories\n\n"
                "Do not upload these files to GitHub, public chats, "
                "or public cloud folders.\n\n"
                "Continue creating reports?"
        )

        return messagebox.askyesno(
                "Privacy warning",
                message,
        )
    def choose_answer_key(self):
        # """
        # Let user choose an answer_key JSON file manually.

        # This is useful if the app was closed after creating the form.
        # """

        file_path = filedialog.askopenfilename(
            title="Choose answer key JSON",
            filetypes=[
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        self.answer_key_var.set(file_path)
        self.answer_key_path = file_path

        self.log("")
        self.log(f"Selected answer key: {file_path}")


    def choose_output_folder(self):
        """
        Let user choose where report files should be saved.
        """

        folder_path = filedialog.askdirectory(
            title="Choose output folder",
        )

        if not folder_path:
            return

        self.output_dir_var.set(folder_path)

        self.log("")
        self.log(f"Selected output folder: {folder_path}")
    def create_reports(self):
        """
        Get Google Form responses and create:
            - report.xlsx
            - detailed_report.xlsx
            - summary_report.pdf

        This method uses:
            - Google Form ID
            - answer_key JSON
            - output folder
        """

        form_id = self.form_id_var.get().strip()
        answer_key_path = self.answer_key_var.get().strip()
        output_dir = self.output_dir_var.get().strip()

        if not form_id:
            messagebox.showwarning(
                "No Form ID",
                "Please enter Google Form ID.",
            )
            return

        if not answer_key_path:
            messagebox.showwarning(
                "No answer key",
                "Please choose answer key JSON file.",
            )
            return

        if not Path(answer_key_path).exists():
            messagebox.showerror(
                "Answer key not found",
                f"Answer key file does not exist:\n{answer_key_path}",
            )
            return

        if not output_dir:
            messagebox.showwarning(
                "No output folder",
                "Please choose output folder.",
            )
            return

        if not self.confirm_privacy_warning():
            self.log("Report creation cancelled by user.")
            return

        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            self.log("")
            self.log("Getting Google credentials...")
            creds = get_credentials()

            self.log("Getting and normalizing responses...")
            normalized_responses = normalize_form_responses(
                form_id=form_id,
                creds=creds,
            )

            self.log(f"Responses found: {len(normalized_responses)}")

            responses_path = "responses_normalized.json"

            save_normalized_responses(
                responses=normalized_responses,
                path=responses_path,
            )

            self.log(f"Normalized responses saved: {responses_path}")

            self.log("Grading responses...")

            graded_results = grade_responses(
                responses_path=responses_path,
                answer_key_path=answer_key_path,
            )

            graded_results_path = "graded_results.json"

            save_json(
                data=graded_results,
                path=graded_results_path,
            )

            self.log(f"Graded responses: {len(graded_results)}")
            self.log(f"Graded results saved: {graded_results_path}")

            self.log("Creating Excel reports...")

            report_path, detailed_report_path = export_reports(
                graded_results=graded_results,
                output_dir=str(output_path),
            )

            self.log(f"Report created: {report_path}")
            self.log(f"Detailed report created: {detailed_report_path}")

            self.log("Creating PDF report...")

            pdf_report_path = export_summary_pdf(
                graded_results=graded_results,
                output_path=str(output_path / "summary_report.pdf"),
            )

            self.log(f"PDF report created: {pdf_report_path}")

            self.log("Cleaning temporary files...")

            deleted_files = cleanup_generated_files()

            self.log(f"Deleted temporary files: {len(deleted_files)}")

            for deleted_file in deleted_files:
                self.log(f"Deleted: {deleted_file}")

            message = (
                "Reports created successfully.\n\n"
                f"Excel report:\n{report_path}\n\n"
                f"Detailed Excel report:\n{detailed_report_path}\n\n"
                f"PDF report:\n{pdf_report_path}\n\n"
                f"Temporary files deleted: {len(deleted_files)}"
            )

            messagebox.showinfo(
                "Reports created",
                message,
            )

        except Exception as error:
            messagebox.showerror(
                "Report error",
                str(error),
            )
            self.log(f"ERROR: {error}")
    def create_form(self):
        """
        Parse the test, create Google Form, and save answer key.
        """

        try:
            parsed_test = self.parse_current_test()

            if parsed_test is None:
                return

            self.log("")
            self.log("Getting Google credentials...")
            creds = get_credentials()

            self.log("Creating Google Form...")
            form_info = create_google_form(
                parsed_test=parsed_test,
                creds=creds,
            )

            self.form_info = form_info

            form_id = form_info["form_id"]
            answer_key_path = self.get_answer_key_output_path(form_id)

            self.log("Saving answer key...")

            save_answer_key(
                parsed_test=parsed_test,
                path=str(answer_key_path),
                thresholds=parsed_test.thresholds,
            )

            self.answer_key_path = str(answer_key_path)
            self.form_id_var.set(form_id)
            self.answer_key_var.set(str(answer_key_path))
            self.log("")
            self.log("Google Form created successfully.")
            self.log(f"Form ID: {form_info['form_id']}")
            self.log(f"Responder URL: {form_info['responder_url']}")
            self.log(f"Edit URL: {form_info['edit_url']}")
            self.log(f"Answer key: {answer_key_path}")
            qr_path = get_qr_code_output_path(form_id)

            saved_qr_path = create_qr_code(
                url=form_info["responder_url"],
                output_path=str(qr_path),
            )

            self.log(f"QR code: {saved_qr_path}")            

            message = (
                "Google Form created successfully.\n\n"
                f"Responder URL:\n{form_info['responder_url']}\n\n"
                f"Edit URL:\n{form_info['edit_url']}\n\n"
                f"Answer key:\n{answer_key_path}\n\n"
                f"QR code:\n{saved_qr_path}"
            )

            messagebox.showinfo(
                "Google Form created",
                message,
            )

        except Exception as error:
            messagebox.showerror(
                "Google Form error",
                str(error),
            )
            self.log(f"ERROR: {error}")