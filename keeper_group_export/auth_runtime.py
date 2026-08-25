"""Keeper Group Export auth runtime module."""

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

class AuthRuntimeMixin:
    def _start_runtime_loader(self):
        """Start the single daemon worker responsible for Keeper imports."""
        self.runtime_started_at = time.perf_counter()
        thread = threading.Thread(target=self._runtime_worker, daemon=True)
        thread.start()
        self.after(75, self._poll_runtime_loader)

    def _runtime_worker(self):
        """Import only the Keeper modules this GUI actually needs.

        The worker performs no Tk operations. Its sole externally-visible effect
        is placing one success/failure tuple on ``runtime_queue``.

        ``keepercommander.__main__`` is deliberately excluded because importing
        the complete Commander CLI stack was the primary invisible-startup cost.
        """
        try:
            from keepercommander import api
            from keepercommander.auth import login_steps
            from keepercommander.config_storage import loader
            from keepercommander.params import KeeperParams
            import platformdirs

            self.runtime_queue.put(
                ("ok", api, login_steps, loader, KeeperParams, platformdirs)
            )
        except Exception as exc:
            self.runtime_queue.put(("error", exc))

    def _poll_runtime_loader(self):
        """Consume the worker result on Tk's main thread without blocking.

        ``after`` polling keeps the event loop responsive. A blocking thread
        join would recreate the original startup freeze.
        """
        try:
            result = self.runtime_queue.get_nowait()
        except queue.Empty:
            self.after(75, self._poll_runtime_loader)
            return

        # Runtime import failure prevents Keeper operations, but the GUI remains
        # alive so the operator receives an explicit diagnostic.
        if result[0] == "error":
            self.runtime_error = result[1]
            self.conn_status.config(text="Keeper library failed to load.", fg=C_DANGER)
            self._set_status("Keeper library failed to load", tone="danger")
            if self.login_overlay is not None:
                self.login_error.config(text=f"Keeper runtime error: {self.runtime_error}")
            return

        # Transfer imported modules/classes into state owned by the Tk thread.
        _, self.k_api, self.k_login_steps, self.k_config_loader, self.k_params_class, self.k_platformdirs = result
        self.runtime_ready = True

        elapsed = time.perf_counter() - self.runtime_started_at
        self.conn_status.config(
            text=f"Keeper library ready • {elapsed:.1f}s",
            fg=C_ACCENT
        )
        self._set_status("Keeper library ready", tone="warning")

        if self.login_overlay is not None:
            self.login_button.config(
                text="Connect",
                state="normal",
                bg=C_ACCENT,
                fg="#111111"
            )
            self.login_hint.config(
                text="Keeper is ready. Enter your account details.",
                fg=C_MUTED
            )

            # If the application has no saved username, populate it from Keeper's
            # existing configuration without importing the full CLI stack.
            if not self.login_user_var.get().strip():
                try:
                    p = self._new_keeper_params()
                    if p.user:
                        self.login_user_var.set(p.user)
                except Exception:
                    pass

    def _keeper_data_dir(self):
        """Resolve Keeper's data directory without importing its CLI entrypoint.

        Precedence mirrors Commander:
        1. explicit KEEPER_DATA_HOME;
        2. existing legacy ~/.keeper;
        3. platform-specific user data + .keeper.

        Reusing Keeper's established data directory allows existing device
        registration/protected configuration to be reused.
        """
        keeper_data_home = os.getenv("KEEPER_DATA_HOME")
        if keeper_data_home:
            path = Path(os.path.expanduser(keeper_data_home))
            if path.name != ".keeper":
                path = path / ".keeper"
            return path

        legacy = Path.home() / ".keeper"
        if legacy.is_dir():
            return legacy

        return Path(self.k_platformdirs.user_data_dir()) / ".keeper"

    def _new_keeper_params(self):
        """Create a fresh KeeperParams object for one authentication attempt.

        Existing configuration is hydrated through Keeper's own config-storage
        layer because modern Commander may protect fields in the OS keychain.

        Config-load failure falls back to fresh parameters. Keeper can then
        request device approval normally; a convenience cache must not become a
        hard availability dependency.
        """
        if not self.runtime_ready:
            raise RuntimeError("Keeper is still loading.")

        data_dir = self._keeper_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        config_file = data_dir / "config.json"

        params = self.k_params_class(config_filename=str(config_file))

        if config_file.is_file():
            try:
                with config_file.open("r", encoding="utf-8") as fh:
                    params.config = json.load(fh)
                self.k_config_loader.load_config_properties(params)
            except Exception:
                # Login can still proceed with fresh params. Keeper will perform
                # any device approval required for a new/unknown client.
                params.config = {}

        if not params.server:
            params.server = "keepersecurity.com"

        return params
