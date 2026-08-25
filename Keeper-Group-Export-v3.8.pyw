"""
Keeper Group Export v3.8
========================

Purpose
-------
Provide a small, auditable Windows GUI for authorised staff who need to export
credential records from one Keeper vault folder to a clean CSV containing only:

    Student, Email, Password

The application is intentionally narrow. It is not a general Keeper client and
does not attempt to reproduce Keeper's editor, sharing model, reports, or full
export formats.

Architecture
------------
The program separates five responsibilities:

1. Immediate presentation
   Tkinter is constructed before Keeper Commander is imported. Keeper has a
   comparatively expensive import graph, so importing it at module load time
   made a valid launch look like a hang. The GUI therefore becomes visible first
   and Keeper is loaded on a background thread.

2. Runtime adaptation
   Keeper Commander remains responsible for authentication, 2FA, cryptography,
   device approval, synchronisation and decryption. This program adapts its
   console-oriented prompts to Tk dialogs rather than reimplementing Keeper's
   security-sensitive protocol.

3. Dynamic vault discovery
   Folder names come from the synchronised Keeper caches. No school year or
   organisational folder is hard-coded as an export boundary. Display labels
   are presentation data; Keeper UIDs remain authoritative identifiers.

4. Record projection
   Records are read directly through Keeper Commander and projected onto the
   deliberately small Student / Email / Password schema. Keeper's own CSV export
   is not used because its columns vary by record type and Commander version.

5. Export
   The preview is a view, not the source of truth. Export re-reads the selected
   Keeper folder and writes UTF-8-with-BOM CSV for reliable Microsoft Excel
   interoperability.

Threading model
---------------
Only Keeper module import occurs off the Tk main thread. Tk widgets are never
created or mutated by the worker. The worker reports through ``runtime_queue``;
Tk polls that queue with ``after()``.

Keeper authentication remains on the Tk thread because Keeper calls the
application's stateful ``LoginUi`` methods, which display modal Tk dialogs for
password, device approval and 2FA.

Security model
--------------
* The master password entered in the login form is copied to
  ``_login_password`` only long enough to satisfy Keeper's password callback.
  The Tk field is cleared before authentication begins and the transient copy is
  cleared when consumed or when authentication fails.
* The utility does not persist the master password.
* Keeper session/key material is owned by Keeper Commander's ``KeeperParams``
  while the process is connected.
* ``settings.json`` contains only the last-used Keeper username.
* The exported CSV deliberately contains plaintext passwords and must therefore
  be protected as credential material.

Deployment context
------------------
The managed Windows environment applies Microsoft Defender ASR rules that block
new, low-prevalence unsigned executables. Normal deployment is therefore:

    VBScript -> Python

PowerShell is used only for first-run/repair runtime preparation.

Maintenance convention
----------------------
Comments document architecture, contracts, state invariants, security
boundaries, compatibility assumptions and failure policy. Obvious widget
geometry is left to the code so the commentary remains useful rather than
becoming a second copy of each statement.
"""

import csv
import json
import logging
import os
import queue
import re
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

# Application identity is centralised so package/file naming can change without
# duplicating version strings throughout the GUI.
APP_TITLE = "Keeper Group Export"
APP_VERSION = "3.8"
APP_SUBTITLE = "Credential Export Utility"
PROGRAMMERS = ("Shannon Smith", "Carlo Cunanan")

# Keeper-inspired presentation palette. These are local visual constants only;
# the program does not inspect or depend on Keeper Desktop UI resources.
C_BG = "#171717"
C_PANEL = "#242424"
C_PANEL_2 = "#2d2d2d"
C_INPUT = "#3a3a3a"
C_BORDER = "#4a4a4a"
C_TEXT = "#f3f3f3"
C_MUTED = "#b6b6b6"
C_ACCENT = "#ffcc00"
C_ACCENT_HOVER = "#ffd633"
C_DANGER = "#e05454"
C_SELECTED = "#555555"
C_SIDEBAR = "#101010"
C_CARD = "#222222"
C_CARD_ALT = "#292929"
C_SUCCESS = "#62d26f"
C_WARNING = "#f0b94d"
C_INFO = "#62a8ff"


def safe_filename(text):
    """Return a Windows-safe filename stem for an exported Keeper folder.

    This sanitises one filename component only. Directory selection remains the
    responsibility of the save dialog.
    """
    text = re.sub(r'[<>:"/\\|?*]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "Keeper-Group"



class KeeperGroupExporter(tk.Tk):
    """Top-level GUI controller and owner of the active Keeper session.

    State invariants
    ----------------
    ``params``
        None until authentication and sync_down have both succeeded.

    ``folder_by_label``
        Presentation label -> Keeper folder UID. Keeper operations always use
        the UID, never the display string.

    ``rows``
        Current preview projection only. Export re-reads Keeper rather than
        treating the Treeview/preview cache as authoritative.

    ``runtime_ready``
        True only after the background import worker has returned all Keeper
        modules required by the GUI.

    ``_login_password``
        One-shot transient bridge between the Tk login form and Keeper's
        getpass callback. It is not persistent credential storage.
    """

    def __init__(self):
        """Construct the first window without importing Keeper Commander."""
        super().__init__()

        self.started_at = time.perf_counter()

        self.title(f"{APP_TITLE} {APP_VERSION}")
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=C_BG)

        # Session-derived state. Empty values here mean "not connected"; no
        # fabricated Keeper folders or records are presented before a real sync.
        self.params = None
        self.folder_by_label = {}
        self.rows = []
        self.filtered_rows = []

        # Preview-only controls. They never change the export contract.
        self.search_var = tk.StringVar()
        self.hide_passwords_var = tk.BooleanVar(value=False)
        self._login_password = ""
        self._device_email_sent = False

        # Keeper module references are populated only by the deferred import
        # worker. This is the central fast-start design decision.
        self.k_api = None
        self.k_params_class = None
        self.k_config_loader = None
        self.k_login_steps = None
        self.k_platformdirs = None
        self.runtime_ready = False
        self.runtime_error = None
        # The worker communicates with Tk exclusively through this thread-safe
        # queue; Tk itself is never touched from the background thread.
        self.runtime_queue = queue.Queue()

        self.last_user = self._read_last_user()

        self._build_styles()
        self._build_ui()
        self.show_login_screen()

        # Let Tk paint the complete application before any Keeper imports occur.
        self.after(50, self._start_runtime_loader)

    def _settings_path(self):
        """Return the per-user convenience-settings path.

        The settings file contains no Keeper master password, session token or
        exported credential data.
        """
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "KeeperGroupExport"
        root.mkdir(parents=True, exist_ok=True)
        return root / "settings.json"

    def _read_last_user(self):
        """Read the last-used username without making startup depend on it.

        Corrupt/missing settings are treated as an empty cache because this file
        is ergonomic state, not authentication state.
        """
        try:
            data = json.loads(self._settings_path().read_text(encoding="utf-8"))
            return (data.get("last_user") or "").strip()
        except Exception:
            return ""

    def _write_last_user(self, user):
        """Persist only the username from the last successful connection.

        Failure is intentionally non-fatal; inability to remember a username
        must not prevent Keeper access or export.
        """
        try:
            self._settings_path().write_text(
                json.dumps({"last_user": user}, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass

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

    def _build_ui(self):
        """Construct the primary application shell.

        The visual hierarchy separates global navigation, vault state, folder
        selection and the record workspace.  Authentication/data loading remains
        outside this method so the window can paint immediately.
        """
        outer = tk.Frame(self, bg=C_BG)
        outer.pack(fill="both", expand=True)

        # ------------------------------------------------------------------
        # Sidebar
        # ------------------------------------------------------------------
        sidebar = tk.Frame(outer, bg=C_SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=C_SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(24, 18))

        badge = tk.Canvas(
            brand, width=38, height=38,
            bg=C_SIDEBAR
        )
        badge.configure(highlightthickness=0)
        badge.create_oval(2, 2, 36, 36, fill=C_ACCENT, outline=C_ACCENT)
        badge.create_text(
            19, 19, text="K",
            fill="#111111", font=("Segoe UI Black", 16)
        )
        badge.pack(side="left")

        brand_text = tk.Frame(brand, bg=C_SIDEBAR)
        brand_text.pack(side="left", padx=(10, 0))
        tk.Label(
            brand_text, text="KEEPER",
            bg=C_SIDEBAR, fg=C_TEXT,
            font=("Segoe UI Semibold", 14),
            anchor="w"
        ).pack(anchor="w")
        tk.Label(
            brand_text, text="GROUP EXPORT",
            bg=C_SIDEBAR, fg="#8f8f8f",
            font=("Segoe UI", 7),
            anchor="w"
        ).pack(anchor="w")

        tk.Label(
            sidebar, text="WORKSPACE",
            bg=C_SIDEBAR