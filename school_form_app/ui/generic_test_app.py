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