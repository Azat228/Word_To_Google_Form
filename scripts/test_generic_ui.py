import tkinter as tk

from school_form_app.ui.generic_test_app import GenericTestApp


def main():
    root = tk.Tk()
    root.title("Generic Test App Test")
    root.geometry("1000x750")

    GenericTestApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()