"""
SCRIPT DESCRIPTION:
This script defines the user interface of the project.
"""

# IMPORTS

import tkinter

# CLASSES

class UserInterface:
    def __init__(self):
        self.root = tkinter.Tk()
        self.root.title("User Interface")
        self.label = tkinter.Label(self.root, text="This is the user interface.")
        self.label.pack(padx=20, pady=20)
        self.root.mainloop()

# GENERAL FUNCTIONS

def test_function():
    print("This is a test function in user_interface.py")
