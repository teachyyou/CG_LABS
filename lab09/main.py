import tkinter as tk
from tkinter import ttk
from app import PolyhedronApp

def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    app = PolyhedronApp(root)
    root.minsize(1280, 780)
    root.mainloop()

if __name__ == "__main__":
    main()
