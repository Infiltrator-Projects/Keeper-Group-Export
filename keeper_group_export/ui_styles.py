"""Keeper Group Export ui styles module."""

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

class UIStylesMixin:
    def _build_styles(self):
        """Configure the deterministic Keeper-inspired ttk presentation.

        ``clam`` is preferred because native Windows ttk themes ignore several
        colour settings. Theme selection is cosmetic and therefore best-effort.
        """
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except Exception:
            pass

        s.configure("Keeper.TFrame", background=C_BG)
        s.configure("Panel.TFrame", background=C_PANEL)
        s.configure("Panel2.TFrame", background=C_PANEL_2)

        s.configure("Keeper.TLabel", background=C_BG, foreground=C_TEXT, font=("Segoe UI", 10))
        s.configure("Title.TLabel", background=C_BG, foreground=C_TEXT, font=("Segoe UI Semibold", 19))
        s.configure("Section.TLabel", background=C_PANEL, foreground=C_TEXT, font=("Segoe UI Semibold", 11))
        s.configure("Muted.TLabel", background=C_BG, foreground=C_MUTED, font=("Segoe UI", 9))
        s.configure("PanelMuted.TLabel", background=C_PANEL, foreground=C_MUTED, font=("Segoe UI", 9))

        s.configure(
            "Accent.TButton",
            background=C_ACCENT,
            foreground="#111111",
            bordercolor=C_ACCENT,
            lightcolor=C_ACCENT,
            darkcolor=C_ACCENT,
            font=("Segoe UI Semibold", 10),
            padding=(14, 8)
        )
        s.map(
            "Accent.TButton",
            background=[("active", C_ACCENT_HOVER), ("disabled", "#6a5d1c")],
            foreground=[("disabled", "#b7ad84")]
        )

        s.configure(
            "Dark.TButton",
            background=C_INPUT,
            foreground=C_TEXT,
            bordercolor=C_BORDER,
            font=("Segoe UI", 10),
            padding=(12, 8)
        )
        s.map(
            "Dark.TButton",
            background=[("active", "#474747"), ("disabled", "#2d2d2d")],
            foreground=[("disabled", "#777777")]
        )

        s.configure(
            "Keeper.TCombobox",
            fieldbackground=C_INPUT,
            background=C_INPUT,
            foreground=C_TEXT,
            arrowcolor=C_TEXT,
            bordercolor=C_BORDER,
            lightcolor=C_BORDER,
            darkcolor=C_BORDER,
            padding=6
        )
        s.map(
            "Keeper.TCombobox",
            fieldbackground=[("readonly", C_INPUT)],
            foreground=[("readonly", C_TEXT)],
            selectbackground=[("readonly", C_INPUT)],
            selectforeground=[("readonly", C_TEXT)]
        )

        s.configure(
            "Keeper.Treeview",
            background=C_PANEL,
            fieldbackground=C_PANEL,
            foreground=C_TEXT,
            rowheight=32,
            bordercolor=C_BORDER,
            lightcolor=C_PANEL,
            darkcolor=C_PANEL
        )
        s.configure(
            "Keeper.Treeview.Heading",
            background=C_PANEL_2,
            foreground=C_TEXT,
            font=("Segoe UI Semibold", 10),
            relief="flat"
        )
        s.map(
            "Keeper.Treeview",
            background=[("selected", C_SELECTED)],
            foreground=[("selected", C_TEXT)]
        )

        s.configure(
            "CardTitle.TLabel",
            background=C_CARD,
            foreground=C_TEXT,
            font=("Segoe UI Semibold", 11)
        )
        s.configure(
            "CardMuted.TLabel",
            background=C_CARD,
            foreground=C_MUTED,
            font=("Segoe UI", 9)
        )
        s.configure(
            "Metric.TLabel",
            background=C_CARD,
            foreground=C_ACCENT,
            font=("Segoe UI Semibold", 18)
        )
        s.configure(
            "Toolbar.TButton",
            background=C_CARD_ALT,
            foreground=C_TEXT,
            bordercolor=C_BORDER,
            font=("Segoe UI", 9),
            padding=(10, 6)
        )
        s.map(
            "Toolbar.TButton",
            background=[("active", "#353535"), ("disabled", C_CARD)],
            foreground=[("disabled", "#707070")]
        )
