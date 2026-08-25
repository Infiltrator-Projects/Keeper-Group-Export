"""Deferred Keeper runtime discovery and configuration loading."""

import json
import os
import queue
import threading
import time
from pathlib import Path

from .common import C_ACCENT, C_DANGER, C_MUTED


class AuthRuntimeMixin:
    def _start_runtime_loader(self):
        """Start the single daemon worker responsible for Keeper imports."""
        self.runtime_started_at = time.perf_counter()
        threading.Thread(target=self._runtime_worker, daemon=True).start()
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
        """Consume the worker result on Tk's main thread without blocking."""
        try:
            result = self.runtime_queue.get_nowait()
        except queue.Empty:
            self.after(75, self._poll_runtime_loader)
            return

        if result[0] == "error":
            self.runtime_error = result[1]
            self.conn_status.config(text="Keeper library failed to load.", fg=C_DANGER)
            self._set_status("Keeper library failed to load", tone="danger")
            if self.login_overlay is not None:
                self.login_error.config(text=f"Keeper runtime error: {self.runtime_error}")
            return

        (
            _,
            self.k_api,
            self.k_login_steps,
            self.k_config_loader,
            self.k_params_class,
            self.k_platformdirs,
        ) = result
        self.runtime_ready = True

        elapsed = time.perf_counter() - self.runtime_started_at
        self.conn_status.config(
            text=f"Keeper library ready • {elapsed:.1f}s",
            fg=C_ACCENT,
        )
        self._set_status("Keeper library ready", tone="warning")

        if self.login_overlay is not None:
            self.login_button.config(
                text="Connect",
                state="normal",
                bg=C_ACCENT,
                fg="#111111",
            )
            self.login_hint.config(
                text="Keeper is ready. Enter your account details.",
                fg=C_MUTED,
            )

            # If no app-local username exists, reuse Keeper's configured account
            # when available. This still persists no password or vault material.
            if not self.login_user_var.get().strip():
                try:
                    params = self._new_keeper_params()
                    if params.user:
                        self.login_user_var.set(params.user)
                except Exception:
                    # Keeper configuration is convenience state; login remains
                    # usable with a manually-entered username if it is unreadable.
                    pass

    def _keeper_data_dir(self):
        """Resolve Keeper's data directory without importing its CLI entrypoint."""
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
        Config-load failure falls back to fresh parameters so device approval can
        proceed normally.
        """
        if not self.runtime_ready:
            raise RuntimeError("Keeper is still loading.")

        data_dir = self._keeper_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        config_file = data_dir / "config.json"

        params = self.k_params_class(config_filename=str(config_file))

        if config_file.is_file():
            try:
                with config_file.open("r", encoding="utf-8") as handle:
                    params.config = json.load(handle)
                self.k_config_loader.load_config_properties(params)
            except (OSError, ValueError, TypeError):
                params.config = {}

        if not params.server:
            params.server = "keepersecurity.com"

        return params
