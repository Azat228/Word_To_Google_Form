"""
Main entry point for the School Form App.

This file starts the new generic UI.

The old UI had separate windows/tabs for different test types.
The new UI uses JSON test templates instead:

    BDI
    BHS
    Burnout
    Ferguson
    future tests...

So now the app opens one generic window where the user chooses
the test template from a dropdown.
"""

import tkinter as tk

from school_form_app.ui.generic_test_app import GenericTestApp


def main():
    """
    Start the desktop application.
    """

    root = tk.Tk()

    root.title("School Form App")
    root.geometry("1100x800")

    GenericTestApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()