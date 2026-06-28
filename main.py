"""Entry point for the desktop application.

This module opens the initial menu window and lets the user choose between
four-option and yes/no test workflows.
"""

import tkinter as tk
from tkinter import ttk

from school_form_app.ui.desktop_app import TestApp
from school_form_app.ui.yes_no_app import YesNoTestApp


class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("School Form App")
        self.root.geometry("500x300")

        self.build_ui()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="Выберите тип теста",
            font=("Arial", 18, "bold"),
        )
        title.pack(pady=30)

        four_option_button = ttk.Button(
            self.root,
            text="4 варианта ответа",
            command=self.open_four_option_app,
        )
        four_option_button.pack(fill="x", padx=60, pady=10)

        yes_no_button = ttk.Button(
            self.root,
            text="ДА / НЕТ с ключом",
            command=self.open_yes_no_app,
        )
        yes_no_button.pack(fill="x", padx=60, pady=10)

        note = ttk.Label(
            self.root,
            text=(
                "4 варианта: например BDI\n"
                "ДА/НЕТ: например шкала безнадёжности Бека"
            ),
            justify="center",
        )
        note.pack(pady=20)

    def open_four_option_app(self):
        window = tk.Toplevel(self.root)
        TestApp(window)

    def open_yes_no_app(self):
        window = tk.Toplevel(self.root)
        YesNoTestApp(window)


def main():
    root = tk.Tk()
    MainMenu(root)
    root.mainloop()


if __name__ == "__main__":
    main()