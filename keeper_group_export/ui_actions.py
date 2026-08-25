"""Keeper Group Export ui actions module."""

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

class UIActionsMixin:
    def refresh_vault(self):
        """Synchronise Keeper again without requiring a new login.

        The current folder UID is preserved when possible. A refresh can expose
        newly-created/renamed folders or changed records while keeping the
        operator in the same workspace.
        """
        if not self.params:
            return

        previous_uid = self.folder_by_label.get(self.group_var.get())

        try:
            self.refresh_btn.config(state="disabled")
            self.conn_status.config(text="Refreshing vault…", fg=C_MUTED)
            self._set_status("Refreshing Keeper vault…", tone="info")
            self.update_idletasks()

            self.k_api.sync_down(self.params)
            self._load_folder_list()

            if previous_uid:
                for label, uid in self.folder_by_label.items():
                    if uid == previous_uid:
                        self.group_var.set(label)
                        self.on_group_selected()
                        break

            self.conn_status.config(
                text=f"Connected • {len(self.folder_by_label)} folders available",
                fg=C_SUCCESS
            )
            self._set_status("Vault refreshed", tone="success")

        except Exception as exc:
            self.conn_status.config(text="Vault refresh failed", fg=C_DANGER)
            self._set_status("Vault refresh failed", tone="danger")
            messagebox.showerror(
                APP_TITLE,
                "Could not refresh the Keeper vault.\n\n" + str(exc),
                parent=self
            )
        finally:
            if self.params:
                self.refresh_btn.config(state="normal")

    def show_about(self):
        """Display product identity, purpose, credits and runtime information."""
        win = tk.Toplevel(self)
        win.title(f"About {APP_TITLE}")
        win.configure(bg=C_BG)
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        card = tk.Frame(
            win, bg=C_CARD,
            highlightbackground="#3b3b3b",
            highlightthickness=1
        )
        card.pack(fill="both", expand=True, padx=16, pady=16)

        badge = tk.Canvas(
            card, width=62, height=62,
            bg=C_CARD, highlightthickness=0
        )
        badge.create_oval(3, 3, 59, 59, fill=C_ACCENT, outline=C_ACCENT)
        badge.create_text(
            31, 31, text="K",
            fill="#111111", font=("Segoe UI Black", 25)
        )
        badge.pack(pady=(22, 8))

        tk.Label(
            card, text=APP_TITLE,
            bg=C_CARD, fg=C_TEXT,
            font=("Segoe UI Semibold", 18)
        ).pack()

        tk.Label(
            card, text=f"{APP_SUBTITLE}  •  Version {APP_VERSION}",
            bg=C_CARD, fg=C_MUTED,
            font=("Segoe UI", 9)
        ).pack(pady=(4, 16))

        body = tk.Frame(card, bg=C_CARD)
        body.pack(fill="x", padx=28)

        tk.Label(
            body,
            text=(
                "Exports credential records from a selected live Keeper folder "
                "to a clean Student / Email / Password CSV."
            ),
            bg=C_CARD, fg=C_TEXT,
            font=("Segoe UI", 9),
            justify="left", wraplength=470
        ).pack(anchor="w")

        tk.Frame(body, bg="#3a3a3a", height=1).pack(fill="x", pady=16)

        tk.Label(
            body, text="PROGRAMMERS",
            bg=C_CARD, fg="#7f7f7f",
            font=("Segoe UI Semibold", 7)
        ).pack(anchor="w")

        tk.Label(
            body,
            text="\n".join(f"• {name}" for name in PROGRAMMERS),
            bg=C_CARD, fg=C_TEXT,
            font=("Segoe UI", 9),
            justify="left"
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            body, text="TECHNOLOGY",
            bg=C_CARD, fg="#7f7f7f",
            font=("Segoe UI Semibold", 7)
        ).pack(anchor="w", pady=(14, 0))

        tk.Label(
            body,
            text="Python 3.13 • Tkinter • Keeper Commander 18.1.2",
            bg=C_CARD, fg=C_TEXT,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(5, 0))

        tk.Label(
            body,
            text=(
                "Independent internal utility. Keeper and Keeper Commander are "
                "products of Keeper Security, Inc."
            ),
            bg=C_CARD, fg="#777777",
            font=("Segoe UI", 8),
            justify="left", wraplength=470
        ).pack(anchor="w", pady=(16, 0))

        tk.Button(
            card, text="Close",
            command=win.destroy,
            bg=C_ACCENT, fg="#111111",
            activebackground=C_ACCENT_HOVER,
            activeforeground="#111111",
            relief="flat", bd=0,
            font=("Segoe UI Semibold", 9),
            padx=20, pady=8
        ).pack(pady=22)

        win.bind("<Escape>", lambda event: win.destroy())

        win.update_idletasks()
        width, height = 550, 470
        x = self.winfo_rootx() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_rooty() + max((self.winfo_height() - height) // 2, 0)
        win.geometry(f"{width}x{height}+{x}+{y}")
