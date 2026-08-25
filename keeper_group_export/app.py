"""Application composition and per-user non-secret settings state."""

import json
import os
import queue
import time
import tkinter as tk
from pathlib import Path

from .auth_flow import AuthFlowMixin
from .auth_present import AuthPresentationMixin
from .auth_runtime import AuthRuntimeMixin
from .common import APP_TITLE, C_BG
from .ui_actions import UIActionsMixin
from .ui_helpers import UIHelpersMixin
from .ui_layout import UILayoutMixin
from .ui_styles import UIStylesMixin
from .vault import VaultMixin


class KeeperGroupExporter(
    UIStylesMixin,
    UILayoutMixin,
    UIHelpersMixin,
    UIActionsMixin,
    AuthRuntimeMixin,
    AuthPresentationMixin,
    AuthFlowMixin,
    VaultMixin,
    tk.Tk,
):
    """Top-level GUI controller and owner of the active Keeper session."""

    def __init__(self):
        """Construct the first window without importing Keeper Commander."""
        super().__init__()

        self.started_at = time.perf_counter()

        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.configure(bg=C_BG)

        # Session-derived state. Empty values here mean "not connected"; no
        # fabricated Keeper folders or records are presented before a real sync.
        self.params = None
        self.folder_by_label = {}
        self.folder_record_index = {}
        self.rows = []
        self.filtered_rows = []

        # Preview-only controls. They never change the export contract.
        self.search_var = tk.StringVar()
        self.hide_passwords_var = tk.BooleanVar(value=False)
        self._login_password = ""

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
        """Read the last-used username without making startup depend on it."""
        try:
            data = json.loads(self._settings_path().read_text(encoding="utf-8"))
            return (data.get("last_user") or "").strip()
        except (OSError, ValueError, TypeError):
            return ""

    def _write_last_user(self, user):
        """Persist only the username from the last successful connection."""
        try:
            self._settings_path().write_text(
                json.dumps({"last_user": user}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            # This file is ergonomic state, not an authentication dependency.
            pass


def main():
    """Start the desktop application."""
    KeeperGroupExporter().mainloop()
