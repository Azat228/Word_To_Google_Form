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
        # -------------------------
        # Option scores
        # -------------------------
        scores_frame = tk.LabelFrame(self.root, text="Стоимость вариантов ответа")
        scores_frame.pack(fill="x", padx=10, pady=5)

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
            text="Скачать QR Code",
            command=self.download_qr_code,
            height=2,
            state="disabled",
        )
        self.qr_button.pack(side="left", fill="x", expand=True, padx=5)
        self.report_button = tk.Button(
            buttons_frame,
            text="3. Получить ответы и создать Excel/PDF",
            command=self.create_report,
            height=2,
            state="disabled",
        )
        self.report_button.pack(side="left", fill="x", expand=True, padx=5)
       
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
        preview_frame = tk.LabelFrame(self.root, text="Preview / Logs")
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.preview_box = tk.Text(preview_frame, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, text: str):
        self.preview_box.insert(tk.END, text + "\n")
        self.preview_box.see(tk.END)
        self.root.update_idletasks()

    def get_option_scores(self) -> list[int]:
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

            self.create_form_button.config(state="normal")

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

    def create_form(self):
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

    def download_qr_code(self):
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
            self.report_button.config(state="disabled", text="Создаю Excel...")
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
            output_path=str(Path(output_dir) / "summary_report.pdf"),
            )

            self.log(f"Краткий отчёт создан: {report_path}")
            self.log(f"Подробный отчёт создан: {detailed_report_path}")
            self.log(f"PDF отчёт создан: {pdf_report_path}")

            self.log("Очистка временных JSON и QR файлов...")

            deleted_files = cleanup_generated_files()

            self.answer_key_path = None

            self.log(f"Удалено файлов: {len(deleted_files)}")

            for deleted_file in deleted_files:
                self.log(f"Удалён: {deleted_file}")

            message = (
                "Отчёты созданы:\n\n"
                f"Краткий Excel отчёт:\n{report_path}\n\n"
                f"Подробный Excel отчёт:\n{detailed_report_path}\n\n"
                f"PDF отчёт:\n{pdf_report_path}\n\n"
                f"Временные JSON/QR файлы удалены: {len(deleted_files)}"
            )

            messagebox.showinfo(
                "Готово",
                message,
            )

        except Exception as error:
            messagebox.showerror("Ошибка", str(error))

        finally:
            self.report_button.config(
                state="normal",
                text="3. Получить ответы и создать Excel",
            )


def main():
    root = tk.Tk()
    TestApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()