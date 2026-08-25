"""Keeper Group Export auth present module."""

import csv
import json
import logging
import os
import queue
import re
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from .common import *

class AuthPresentationMixin:
    def show_login_screen(self):
        """Present the login overlay unless one is already active.

        Username may be pre-filled. Master password is never persisted or
        pre-populated.
        """
        if self.login_overlay is not None:
            return

        overlay = tk.Frame(self.main, bg=C_BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()
        self.login_overlay = overlay

        card = tk.Frame(
            overlay, bg=C_PANEL,
            highlightbackground=C_BORDER, highlightthickness=1
        )
        # Keep a dedicated vertical reserve for validation/authentication errors.
        # The earlier 370 px card clipped the error label below the Connect button.
        card.place(relx=0.5, rely=0.46, anchor="center", width=470, height=430)

        badge = tk.Canvas(card, width=54, height=54, bg=C_PANEL, highlightthickness=0)
        badge.create_oval(2, 2, 52, 52, fill=C_ACCENT, outline=C_ACCENT)
        badge.create_text(27, 27, text="K", fill="#111111", font=("Segoe UI Black", 23))
        badge.pack(pady=(24, 8))

        tk.Label(
            card, text="Sign in to Keeper",
            bg=C_PANEL, fg=C_TEXT,
            font=("Segoe UI Semibold", 16)
        ).pack()

        self.login_hint = tk.Label(
            card,
            text="Preparing Keeper in the background…" if not self.runtime_ready
                 else "Enter your Keeper account details.",
            bg=C_PANEL, fg=C_MUTED, font=("Segoe UI", 9)
        )
        self.login_hint.pack(pady=(4, 16))

        form = tk.Frame(card, bg=C_PANEL)
        form.pack(fill="x", padx=36)

        tk.Label(form, text="Email", bg=C_PANEL, fg=C_MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        self.login_user_var = tk.StringVar(value=self.last_user)
        user_entry = tk.Entry(
            form, textvariable=self.login_user_var,
            bg=C_INPUT, fg=C_TEXT, insertbackground=C_TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=C_BORDER, highlightcolor=C_ACCENT,
            font=("Segoe UI", 10)
        )
        user_entry.pack(fill="x", ipady=8, pady=(4, 10))

        tk.Label(form, text="Master password", bg=C_PANEL, fg=C_MUTED, font=("Segoe UI", 9)).pack(anchor="w")
        self.login_password_var = tk.StringVar()
        pass_entry = tk.Entry(
            form, textvariable=self.login_password_var,
            show="•",
            bg=C_INPUT, fg=C_TEXT, insertbackground=C_TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=C_BORDER, highlightcolor=C_ACCENT,
            font=("Segoe UI", 10)
        )
        pass_entry.pack(fill="x", ipady=8, pady=(4, 14))

        self.login_button = tk.Button(
            form,
            text="Preparing Keeper…" if not self.runtime_ready else "Connect",
            bg="#6a5d1c" if not self.runtime_ready else C_ACCENT,
            fg="#b7ad84" if not self.runtime_ready else "#111111",
            activebackground=C_ACCENT_HOVER,
            activeforeground="#111111",
            relief="flat", bd=0,
            font=("Segoe UI Semibold", 10),
            command=self._start_connect_from_login,
            state="disabled" if not self.runtime_ready else "normal"
        )
        self.login_button.pack(fill="x", ipady=7)

        # Reserve an error area inside the card so long authentication messages
        # remain visible instead of being clipped below the fixed card boundary.
        self.login_error = tk.Label(
            card, text="", bg=C_PANEL, fg=C_DANGER,
            font=("Segoe UI", 8), wraplength=395,
            justify="left", anchor="n"
        )
        self.login_error.pack(fill="x", padx=36, pady=(10, 10))

        pass_entry.bind("<Return>", lambda e: self._start_connect_from_login())
        user_entry.bind("<Return>", lambda e: pass_entry.focus_set())
        user_entry.focus_set() if not self.last_user else pass_entry.focus_set()

    def _start_connect_from_login(self):
        """Validate form data and enter the Keeper authentication flow.

        The password widget is cleared before network activity begins. A single
        transient copy remains only for Keeper's first getpass request.
        """
        if not self.runtime_ready:
            self.login_error.config(text="Keeper is still preparing.")
            return

        user = self.login_user_var.get().strip()
        password = self.login_password_var.get()

        if not user or not password:
            self.login_error.config(text="Enter your Keeper email and master password.")
            return

        self._login_password = password
        self.login_password_var.set("")
        self.login_button.config(state="disabled", text="Connecting…")
        self.login_error.config(text="")
        self.update_idletasks()

        self.connect_keeper(user)

    def _choose_from_list(self, title, prompt, choices):
        """Return a zero-based selection from a modal list, or None on cancel."""
        result = {"index": None}

        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=C_PANEL)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        tk.Label(
            win, text=prompt, bg=C_PANEL, fg=C_TEXT,
            font=("Segoe UI Semibold", 10),
            justify="left", wraplength=430
        ).pack(fill="x", padx=18, pady=(18, 10))

        listbox = tk.Listbox(
            win, height=min(max(len(choices), 2), 8),
            bg=C_INPUT, fg=C_TEXT,
            selectbackground=C_SELECTED, selectforeground=C_TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=C_BORDER,
            font=("Segoe UI", 10), activestyle="none"
        )
        listbox.pack(fill="both", expand=True, padx=18)

        for choice in choices:
            listbox.insert("end", choice)

        if choices:
            listbox.selection_set(0)
            listbox.activate(0)

        buttons = tk.Frame(win, bg=C_PANEL)
        buttons.pack(fill="x", padx=18, pady=16)

        def accept():
            selection = listbox.curselection()
            if selection:
                result["index"] = int(selection[0])
            win.destroy()

        def cancel():
            win.destroy()

        tk.Button(
            buttons, text="Cancel", command=cancel,
            bg=C_INPUT, fg=C_TEXT, activebackground="#474747",
            activeforeground=C_TEXT, relief="flat", bd=0,
            font=("Segoe UI", 9), padx=16, pady=7
        ).pack(side="right")

        tk.Button(
            buttons, text="Continue", command=accept,
            bg=C_ACCENT, fg="#111111", activebackground=C_ACCENT_HOVER,
            activeforeground="#111111", relief="flat", bd=0,
            font=("Segoe UI Semibold", 9), padx=16, pady=7
        ).pack(side="right", padx=(0, 8))

        listbox.bind("<Double-Button-1>", lambda event: accept())
        listbox.bind("<Return>", lambda event: accept())
        win.protocol("WM_DELETE_WINDOW", cancel)

        win.update_idletasks()
        x = self.winfo_rootx() + max((self.winfo_width() - win.winfo_reqwidth()) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - win.winfo_reqheight()) // 2, 0)
        win.geometry(f"+{x}+{y}")

        self.wait_window(win)
        return result["index"]
