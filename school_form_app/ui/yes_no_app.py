"""Tkinter workflow for the yes/no keyed test application.

The UI collects the scoring key, parses a Word document, creates a Google
Form, and builds the reporting artifacts for the test results.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from school_form_app.parsing.yes_no_keyed_parser import (
    parse_yes_no_keyed_docx,
    parse_question_numbers,
)
from school_form_app.google_api.auth import get_credentials
from school_form_app.google_api.forms import create_google_form
from school_form_app.google_api.responses import (
    normalize_form_responses,
    save_normalized_responses,
)
from school_form_app.reports.answer_key import save_answer_key
from school_form_app.reports.grading import grade_responses, save_json
from school_form_app.reports.excel_export import export_reports
from school_form_app.reports.pdf_export import export_summary_pdf
from school_form_app.reports.cleanup import cleanup_generated_files
from school_form_app.reports.qr_code import (
    create_qr_code,
    make_google_form_responder_url,
)
from school_form_app.models import GradeThreshold


class YesNoTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Yes/No Keyed Test App")
        self.root.geometry("950x750")

        self.docx_path = None
        self.parsed_test = None
        self.form_id = None
        self.answer_key_path = None

        self.build_ui()

    def build_ui(self):
        # Build the main window layout in stages: first the scoring key inputs,
        # then the report thresholds, then the action buttons and preview panel.
        # This keeps the workflow intuitive and grouped by responsibility.
        key_frame = tk.LabelFrame(
            self.root,
            text="Ключ обработки ДА/НЕТ",
        )
        key_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(key_frame, text="ДА = 1 балл для вопросов:").grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        # The yes/no scoring key is entered as question numbers that should add
        # one point when the student answers positively or negatively.
        self.yes_key_entry = tk.Entry(key_frame)
        self.yes_key_entry.insert(0, "1,3,5,6,8,10,11,13,15,19")
        self.yes_key_entry.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        tk.Label(key_frame, text="НЕТ = 1 балл для вопросов:").grid(
            row=1,
            column=0,
            padx=5,
            pady=5,
            sticky="w",
        )

        # The no-key field is parsed separately so the app can validate that no
        # question appears in both scoring sets at the same time.
        self.no_key_entry = tk.Entry(key_frame)
        self.no_key_entry.insert(0, "2,4,7,9,12,14,16,17,18,20")
        self.no_key_entry.grid(
            row=1,
            column=1,
            padx=5,
            pady=5,
            sticky="ew",
        )

        key_frame.columnconfigure(1, weight=1)

        # Thresholds define how the final score is translated into a qualitative
        # label such as "normal", "mild", or "severe".
        thresholds_frame = tk.LabelFrame(
            self.root,
            text="Градации отчёта. Формат: min-max=Название",
        )
        thresholds_frame.pack(fill="x", padx=10, pady=5)

        self.thresholds_text = tk.Text(thresholds_frame, height=5)
        self.thresholds_text.pack(fill="x", padx=5, pady=5)

        self.thresholds_text.insert(
            "1.0",
            "0-3=Норма\n"
            "4-8=Лёгкая степень безнадёжности\n"
            "9-14=Умеренная степень безнадёжности\n"
            "15-20=Тяжёлая степень безнадёжности\n",
        )

        # The action buttons represent the main pipeline of the app:
        # 1) load a Word document, 2) create a Google Form, 3) generate reports.
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(fill="x", padx=10, pady=5)

        self.select_button = tk.Button(
            buttons_frame,
            text="1. Выбрать Word файл",
            command=self.select_word_file,
            height=2,
        )
        self.select_button.pack(side="left", fill="x", expand=True, padx=5)

        self.create_form_button = tk.Button(
            buttons_frame,
            text="2. Создать Google Form",
            command=self.create_form,
            height=2,
            state="disabled",
        )
        self.create_form_button.pack(side="left", fill="x", expand=True, padx=5)

        self.qr_button = tk.Button(
            buttons_frame,
            text="3. Скачать QR Code",
            command=self.download_qr_code,
            height=2,
            state="disabled",
        )
        self.qr_button.pack(side="left", fill="x", expand=True, padx=5)

        self.report_button = tk.Button(
            buttons_frame,
            text="4. Получить ответы и создать Excel/PDF",
            command=self.create_report,
            height=2,
            state="disabled",
        )
        self.report_button.pack(side="left", fill="x", expand=True, padx=5)

        self.clear_cache_button = tk.Button(
            buttons_frame,
            text="5. Очистить кэш",
            command=self.clear_cache,
            height=2,
            state="disabled",
        )
        self.clear_cache_button.pack(side="left", fill="x", expand=True, padx=5)

        form_frame = tk.LabelFrame(self.root, text="Google Form ID")
        form_frame.pack(fill="x", padx=10, pady=5)

        self.form_id_entry = tk.Entry(form_frame)
        self.form_id_entry.pack(fill="x", padx=5, pady=5)

        preview_frame = tk.LabelFrame(self.root, text="Просмотр / Логи")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # The preview area acts as a live log and inspection panel, showing the
        # parsed test content and the status of each processing step.
        self.preview_box = tk.Text(preview_frame, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, text: str):
        # Append each status message to the text widget and keep the view at the
        # bottom so the user sees the latest progress immediately.
        self.preview_box.insert(tk.END, text + "\n")
        self.preview_box.see(tk.END)
        self.root.update_idletasks()

    def get_yes_no_key(self) -> tuple[set[int], set[int]]:
        # Convert the user-entered question ranges into sets of numbers so the
        # parser can quickly check whether each question belongs to the yes or no
        # scoring group.
        yes_score_questions = parse_question_numbers(
            self.yes_key_entry.get()
        )

        no_score_questions = parse_question_numbers(
            self.no_key_entry.get()
        )

        overlap = yes_score_questions.intersection(no_score_questions)

        if overlap:
            raise ValueError(
                f"Эти вопросы есть и в ДА, и в НЕТ ключе: {sorted(overlap)}"
            )

        return yes_score_questions, no_score_questions

    def get_thresholds(self) -> list[GradeThreshold]:
        # Parse the threshold text field line by line and turn each range into a
        # structured object that the grading logic can use later.
        raw_text = self.thresholds_text.get("1.0", tk.END).strip()
        thresholds = []

        if not raw_text:
            return thresholds

        for line in raw_text.splitlines():
            line = line.strip()

            if not line:
                continue

            if "=" not in line or "-" not in line:
                raise ValueError(
                    f"Неверный формат градации: {line}\n"
                    "Используй формат: 0-3=Норма"
                )

            range_part, label = line.split("=", 1)
            min_part, max_part = range_part.split("-", 1)

            threshold = GradeThreshold(
                min_score=int(min_part.strip()),
                max_score=int(max_part.strip()),
                label=label.strip(),
            )

            thresholds.append(threshold)

        return thresholds

    def select_word_file(self):
        # Let the user select a .docx file, parse it using the yes/no rules, and
        # preview the resulting test structure before creating a form.
        file_path = filedialog.askopenfilename(
            title="Выберите Word файл",
            filetypes=[
                ("Word documents", "*.docx"),
                ("All files", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            yes_key, no_key = self.get_yes_no_key()
            thresholds = self.get_thresholds()

            self.docx_path = Path(file_path)

            self.parsed_test = parse_yes_no_keyed_docx(
                str(self.docx_path),
                yes_score_questions=yes_key,
                no_score_questions=no_key,
            )

            self.parsed_test.thresholds = thresholds

            self.preview_box.delete("1.0", tk.END)

            self.log(f"Файл: {self.docx_path}")
            self.log(f"Название: {self.parsed_test.title}")
            self.log(f"Количество вопросов: {len(self.parsed_test.questions)}")
            self.log("")

            for question in self.parsed_test.questions:
                self.log(f"{question.number}. {question.title}")

                for option in question.options:
                    self.log(f"   [{option.score}] {option.text}")

                self.log("")

            self.create_form_button.config(state="normal")
            # Keep report and cache buttons disabled until a new form/report flow completes
            self.report_button.config(state="disabled")
            self.clear_cache_button.config(
                state="disabled",
                text="Очистить кэш",
            )

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

    def create_form(self):
        # Create the Google Form from the parsed test, save the answer-key JSON,
        # and unlock the next actions so the user can generate reports.
        if self.parsed_test is None:
            messagebox.showwarning("Нет теста", "Сначала выберите Word файл.")
            return

        try:
            self.create_form_button.config(state="disabled", text="Создаю...")
            self.root.update_idletasks()

            thresholds = self.get_thresholds()

            self.log("Авторизация Google...")
            creds = get_credentials()

            self.log("Создание Google Form...")
            form_info = create_google_form(self.parsed_test, creds)

            self.form_id = form_info["form_id"]
            self.form_id_entry.delete(0, tk.END)
            self.form_id_entry.insert(0, self.form_id)

            answer_keys_dir = Path("answer_keys")
            answer_keys_dir.mkdir(parents=True, exist_ok=True)

            self.answer_key_path = str(
                answer_keys_dir / f"answer_key_{self.form_id}.json"
            )

            save_answer_key(
                self.parsed_test,
                path=self.answer_key_path,
                option_scores=None,
                thresholds=thresholds,
            )

            self.log("")
            self.log("Google Form создана.")
            self.log(f"Form ID: {self.form_id}")
            self.log(f"Responder URL: {form_info['responder_url']}")
            self.log(f"Edit URL: {form_info['edit_url']}")
            self.log(f"Answer key: {self.answer_key_path}")

            messagebox.showinfo(
                "Готово",
                "Google Form создана.\n\n"
                f"Responder URL:\n{form_info['responder_url']}\n\n"
                f"Answer key:\n{self.answer_key_path}",
            )

            self.report_button.config(state="normal")
            self.qr_button.config(state="normal")

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

        finally:
            self.create_form_button.config(
                state="normal",
                text="2. Создать Google Form",
            )

    def download_qr_code(self):
        # Build the responder URL from the form ID and export a QR code image so
        # the form can be shared quickly in a classroom or by email.
        form_id = self.form_id_entry.get().strip()

        if not form_id:
            messagebox.showwarning(
                "Нет Form ID",
                "Сначала создай Google Form или вставь Form ID вручную.",
            )
            return

        try:
            self.qr_button.config(state="disabled", text="Создаю QR Code...")
            self.root.update_idletasks()
            responder_url = make_google_form_responder_url(form_id)

            output_path = filedialog.asksaveasfilename(
                title="Сохранить QR Code",
                defaultextension=".png",
                filetypes=[
                    ("PNG image", "*.png"),
                ],
                initialfile=f"qr_code_{form_id}.png",
            )

            if not output_path:
                self.log("Сохранение QR Code отменено.")
                return

            create_qr_code(
                url=responder_url,
                output_path=output_path,
            )

            self.log(f"QR Code создан: {output_path}")

            messagebox.showinfo(
                "Готово",
                f"QR Code сохранён:\n{output_path}",
            )

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))
        finally:
            self.qr_button.config(state="normal", text="Скачать QR Code")

    def clear_cache(self):
        # Remove temporary JSON and QR files produced during the workflow while
        # keeping the authentication files protected.
        self.log("Очистка временных JSON и QR файлов...")

        deleted_files = cleanup_generated_files()
        self.answer_key_path = None

        if deleted_files:
            self.log(f"Удалено файлов: {len(deleted_files)}")
            for deleted_file in deleted_files:
                self.log(f"Удалён: {deleted_file}")
        else:
            self.log("Файлы для очистки не найдены.")

        self.clear_cache_button.config(
            state="disabled",
            text="Загрузите новый Word файл",
        )
        self.report_button.config(
            state="disabled",
            text="Загрузите новый Word файл",
        )
        self.qr_button.config(
            state="disabled",   
            text="Загрузите новый Word файл",
        )
        self.create_form_button.config(
            state="disabled",
            text="Загрузите новый Word файл",
        )

        message = (
            "Кэш очищен. Удалены временные JSON и QR файлы, кроме credentials и token.\n\n"
            f"Удалено файлов: {len(deleted_files)}"
        )

        messagebox.showinfo(
            "Готово",
            message,
        )

    def create_report(self):
        # Pull responses from the Google Form, normalize them, grade them with
        # the saved answer key, and export Excel and PDF reports for review.
        form_id = self.form_id_entry.get().strip()

        if not form_id:
            messagebox.showwarning("Нет Form ID", "Введите Google Form ID.")
            return

        answer_key_path = self.answer_key_path

        if not answer_key_path:
            possible_path = str(
                Path("answer_keys") / f"answer_key_{form_id}.json"
            )

            if Path(possible_path).exists():
                answer_key_path = possible_path
            else:
                selected = filedialog.askopenfilename(
                    title="Выберите answer_key JSON",
                    filetypes=[
                        ("JSON files", "*.json"),
                        ("All files", "*.*"),
                    ],
                )

                if not selected:
                    return

                answer_key_path = selected

        try:
            self.report_button.config(state="disabled", text="Создаю Excel/PDF...")
            self.root.update_idletasks()

            self.log("")
            self.log("Авторизация Google...")
            creds = get_credentials()

            self.log("Получение ответов...")
            normalized = normalize_form_responses(form_id, creds)
            save_normalized_responses(normalized, "responses_normalized.json")

            self.log(f"Ответов найдено: {len(normalized)}")

            self.log("Подсчёт баллов...")
            graded_results = grade_responses(
                responses_path="responses_normalized.json",
                answer_key_path=answer_key_path,
            )

            save_json(graded_results, "graded_results.json")

            output_dir = filedialog.askdirectory(
                title="Выберите папку для сохранения отчётов"
            )

            if not output_dir:
                self.log("Сохранение Excel отменено.")
                return

            self.log("Создание Excel отчётов...")

            report_path, detailed_report_path = export_reports(
                graded_results=graded_results,
                output_dir=output_dir,
            )
            pdf_report_path = export_summary_pdf(
                graded_results=graded_results,
                output_path=str(Path(output_dir) / "PDF_отчет.pdf"),
            )

            self.log(f"Краткий отчёт создан: {report_path}")
            self.log(f"Подробный отчёт создан: {detailed_report_path}")
            self.log(f"PDF отчёт создан: {pdf_report_path}")

            self.clear_cache_button.config(state="normal")

            message = (
                "Отчёты созданы:\n\n"
                f"Краткий Excel отчёт:\n{report_path}\n\n"
                f"Подробный Excel отчёт:\n{detailed_report_path}\n\n"
                f"PDF отчёт:\n{pdf_report_path}\n\n"
                "Теперь можно очистить кэш, чтобы удалить временные JSON и QR файлы."
            )

            messagebox.showinfo(
                "Готово",
                message,
            )

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

        finally:
            self.report_button.config(
                state="normal" if self.form_id and answer_key_path else "disabled",
                text="3. Получить ответы и создать Excel/PDF",
            )


def main():
    root = tk.Tk()
    YesNoTestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()