import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

from parser_docx import parse_docx
from google_auth import get_credentials
from google_forms import create_google_form
from answer_key import save_answer_key


class WordToGoogleFormApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Word to Google Form")
        self.root.geometry("800x600")

        self.docx_path = None
        self.parsed_test = None

        self.select_button = tk.Button(
            root,
            text="Выбрать Word файл",
            command=self.select_word_file,
            height=2,
        )
        self.select_button.pack(fill="x", padx=10, pady=10)

        self.preview_box = tk.Text(root, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_button = tk.Button(
            root,
            text="Создать Google Form",
            command=self.create_form,
            height=2,
            state="disabled",
        )
        self.create_button.pack(fill="x", padx=10, pady=10)

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

        self.docx_path = Path(file_path)

        try:
            self.parsed_test = parse_docx(str(self.docx_path))
        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось прочитать Word файл:\n{error}")
            return

        self.show_preview()
        self.create_button.config(state="normal")

    def show_preview(self):
        self.preview_box.delete("1.0", tk.END)

        self.preview_box.insert(tk.END, f"Название: {self.parsed_test.title}\n")
        self.preview_box.insert(
            tk.END,
            f"Количество вопросов: {len(self.parsed_test.questions)}\n\n",
        )

        for index, question in enumerate(self.parsed_test.questions, start=1):
            self.preview_box.insert(tk.END, f"{index}. {question.text}\n")

            for option in question.options:
                if option == question.correct_answer:
                    self.preview_box.insert(tk.END, f"   - {option}  <-- correct\n")
                else:
                    self.preview_box.insert(tk.END, f"   - {option}\n")

            self.preview_box.insert(tk.END, "\n")

    def create_form(self):
        if self.parsed_test is None:
            messagebox.showwarning("Нет файла", "Сначала выберите Word файл.")
            return

        confirm = messagebox.askyesno(
            "Подтверждение",
            "Создать Google Form из этого Word файла?",
        )

        if not confirm:
            return

        try:
            self.create_button.config(state="disabled", text="Создаю форму...")
            self.root.update_idletasks()

            creds = get_credentials()
            form_info = create_google_form(self.parsed_test, creds)

            answer_key_path = f"answer_key_{form_info['form_id']}.json"
            save_answer_key(self.parsed_test, answer_key_path)

            result_message = (
                "Google Form создана.\n\n"
                f"Responder URL:\n{form_info['responder_url']}\n\n"
                f"Edit URL:\n{form_info['edit_url']}\n\n"
                f"Answer key сохранён:\n{answer_key_path}"
            )

            messagebox.showinfo("Готово", result_message)

            self.preview_box.insert(tk.END, "\n=== GOOGLE FORM CREATED ===\n")
            self.preview_box.insert(
                tk.END,
                f"Responder URL: {form_info['responder_url']}\n",
            )
            self.preview_box.insert(
                tk.END,
                f"Edit URL: {form_info['edit_url']}\n",
            )
            self.preview_box.insert(
                tk.END,
                f"Answer key: {answer_key_path}\n",
            )

        except Exception as error:
            messagebox.showerror("Ошибка", f"Не удалось создать Google Form:\n{error}")

        finally:
            self.create_button.config(state="normal", text="Создать Google Form")


def main():
    root = tk.Tk()
    app = WordToGoogleFormApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()