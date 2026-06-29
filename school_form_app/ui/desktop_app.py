"""Tkinter workflow for the four-option test application.

This module builds the main form-processing interface, including score entry,
threshold configuration, Google Form creation, and report generation.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from school_form_app.parsing.docx_parser import parse_docx
from school_form_app.google_api.auth import get_credentials
from school_form_app.google_api.forms import create_google_form
from school_form_app.google_api.responses import (
    normalize_form_responses,
    save_normalized_responses,
)
from school_form_app.reports.answer_key import save_answer_key
from school_form_app.reports.grading import grade_responses, save_json
from school_form_app.reports.excel_export import export_reports
from school_form_app.reports.cleanup import cleanup_generated_files
from school_form_app.models import GradeThreshold
from school_form_app.reports.qr_code import (
    create_qr_code,
    make_google_form_responder_url,
)
from school_form_app.reports.pdf_export import export_summary_pdf
class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word to Google Form Report App")
        self.root.geometry("950x750")

        self.docx_path = None
        self.parsed_test = None
        self.form_id = None
        self.answer_key_path = None

        self.build_ui()

    def build_ui(self):
        # Construct the full desktop interface by grouping the score settings,
        # threshold configuration, action buttons, and result preview into a
        # logical layout for the four-option test flow.
        # -------------------------
        # Option scores
        # -------------------------
        scores_frame = tk.LabelFrame(self.root, text="Стоимость вариантов ответа")
        scores_frame.pack(fill="x", padx=10, pady=5)

        # Each entry box corresponds to one of the four possible answer choices,
        # so the user can define the score assigned to each option.
        self.score_entries = []

        default_scores = ["0", "1", "2", "3"]

        for index in range(4):
            label = tk.Label(scores_frame, text=f"{index + 1}-й вариант:")
            label.grid(row=0, column=index * 2, padx=5, pady=5)

            entry = tk.Entry(scores_frame, width=6)
            entry.insert(0, default_scores[index])
            entry.grid(row=0, column=index * 2 + 1, padx=5, pady=5)

            self.score_entries.append(entry)

        # -------------------------
        # Thresholds
        # -------------------------
        thresholds_frame = tk.LabelFrame(
            self.root,
            text="Градации отчёта. Формат: min-max=Название",
        )
        thresholds_frame.pack(fill="x", padx=10, pady=5)

        # The threshold editor lets the user describe score ranges and the label
        # that should appear in the final report for each range.
        self.thresholds_text = tk.Text(thresholds_frame, height=5)
        self.thresholds_text.pack(fill="x", padx=5, pady=5)

        self.thresholds_text.insert(
            "1.0",
            "0-9=Минимальный уровень\n"
            "10-18=Лёгкая степень\n"
            "19-29=Умеренная степень\n"
            "30-63=Выраженная степень\n",
        )

        # -------------------------
        # Buttons
        # -------------------------
        # Buttons represent the main pipeline: choose a Word test, create a form,
        # generate QR access, and produce reports once responses arrive.
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
            text="3.Скачать QR Code",
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
       
        # -------------------------
        # Form ID manual field
        # -------------------------
        form_frame = tk.LabelFrame(self.root, text="Google Form ID")
        form_frame.pack(fill="x", padx=10, pady=5)

        self.form_id_entry = tk.Entry(form_frame)
        self.form_id_entry.pack(fill="x", padx=5, pady=5)

        # -------------------------
        # Preview
        # -------------------------
        preview_frame = tk.LabelFrame(self.root, text="Просмотр / Логи")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # The preview pane shows the parsed document content and a running log of
        # the actions completed by the app.
        self.preview_box = tk.Text(preview_frame, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, text: str):
        # Add each status message to the preview area so the user can follow the
        # workflow step by step without leaving the window.
        self.preview_box.insert(tk.END, text + "\n")
        self.preview_box.see(tk.END)
        self.root.update_idletasks()

    def get_option_scores(self) -> list[int]:
        # Read all score entry fields and validate them before passing them to
        # the parser, which uses them to assign points to each answer option.
        scores = []

        for entry in self.score_entries:
            value = entry.get().strip()

            if not value:
                raise ValueError("Стоимость варианта не может быть пустой.")

            scores.append(int(value))

        if len(scores) != 4:
            raise ValueError("Нужно ровно 4 стоимости вариантов.")

        return scores

    def get_thresholds(self) -> list[GradeThreshold]:
        # Parse the threshold editor into structured objects so the report layer
        # can later map total scores to human-readable labels.
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
                    "Используй формат: 0-9=Минимальный уровень"
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
        # Open a Word file, parse it into question/option objects, and preview the
        # extracted content before the form is created.
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
            option_scores = self.get_option_scores()
            thresholds = self.get_thresholds()

            self.docx_path = Path(file_path)

            self.parsed_test = parse_docx(
                str(self.docx_path),
                option_scores=option_scores,
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
            # Ensure report and cache clear buttons stay disabled until the next flow.
            self.clear_cache_button.config(
                state="disabled",
                text="5. Очистить кэш",
            )
            self.report_button.config(
            state="disabled",
            text="4. Получить ответы и создать Excel/PDF",
            )
            self.qr_button.config(
            state="disabled",   
            text="3. Создать QR код",
            )
            self.create_form_button.config(
            state="normal",
            text="2. Создать Google Form",
            )

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

    def create_form(self):
        # Turn the parsed test into a Google Form, create a matching answer key,
        # and prepare a QR code for quick sharing.
        if self.parsed_test is None:
            messagebox.showwarning("Нет теста", "Сначала выберите Word файл.")
            return

        try:
            self.create_form_button.config(state="disabled", text="Создаю...")
            self.root.update_idletasks()

            option_scores = self.get_option_scores()
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
            qr_code_path = f"qr_code_{self.form_id}.png"
            save_answer_key(
                self.parsed_test,
                path=self.answer_key_path,
                option_scores=option_scores,
                thresholds=thresholds,
            )

            create_qr_code(
                url=form_info["responder_url"],
                output_path=qr_code_path,
            )

            self.log("")
            self.log("Google Form создана.")
            self.log(f"Form ID: {self.form_id}")
            self.log(f"Responder URL: {form_info['responder_url']}")
            self.log(f"Edit URL: {form_info['edit_url']}")
            self.log(f"Answer key: {self.answer_key_path}")
            self.log(f"QR code: {qr_code_path}")

            messagebox.showinfo(
                "Готово",
                "Google Form создана.\n\n"
                f"Responder URL:\n{form_info['responder_url']}\n\n"
                f"QR code:\n{qr_code_path}\n\n"
                f"Answer key:\n{self.answer_key_path}",
            )

            self.report_button.config(state="normal")
            self.qr_button.config(state="normal")

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

        finally:
            self.create_form_button.config(state="normal", text="2. Создать Google Form")

    def clear_cache(self):
        # Remove temporary files produced during earlier steps so the workspace
        # stays tidy and the user can start a fresh run.
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

    def download_qr_code(self):
        # Recreate the QR code from a stored form ID when the user wants to share
        # the form again without generating it from scratch.
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

    def create_report(self):
        # Retrieve Google Form responses, convert them into a normalized format,
        # grade them, and export both Excel and PDF reports.
        form_id = self.form_id_entry.get().strip()

        if not form_id:
            messagebox.showwarning("Нет Form ID", "Введите Google Form ID.")
            return

        answer_key_path = self.answer_key_path

        if not answer_key_path:
            possible_path = str(Path("answer_keys") / f"answer_key_{form_id}.json")

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
                text="4. Получить ответы и создать Excel/PDF",
            )


def main():
    root = tk.Tk()
    TestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()