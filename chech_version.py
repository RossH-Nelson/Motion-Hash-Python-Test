import tkinter as tk

# Get the Tkinter version
print("Tkinter version:", tk.TkVersion)

# Check where Tkinter is installed
import os
tkinter_path = os.path.dirname(tk.__file__)
print("Tkinter is installed at:", tkinter_path)
