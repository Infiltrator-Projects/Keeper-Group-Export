"""Keeper Group Export vault module."""

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

class VaultMixin:
    def _descendant_folder_uids(self, root_uid):
        """Return ``root_uid`` plus every reachable descendant folder UID.

        Keeper folders should be acyclic; ``seen`` is defensive protection
        against malformed cache state causing unbounded recursion.
        """
        result = []
        seen = set()

        def walk(uid):
            """Depth-first traversal over Keeper's cached child-folder UID links."""
            if uid in seen:
                return
            seen.add(uid)
            result.append(uid)
            folder = self.params.folder_cache.get(uid)
            if folder:
                for child_uid in getattr(folder, "subfolders", []) or []:
                    walk(child_uid)

        walk(root_uid)
        return result

    def _record_uids_for_folder(self, root_uid):
        """Return de-duplicated record UIDs for a folder subtree.

        A set is intentional because Keeper records may be linked into multiple
        folders. Export semantics are one row per underlying Keeper record UID,
        not one row per folder reference.
        """
        record_uids = set()
        for folder_uid in self._descendant_folder_uids(root_uid):
            record_uids.update(
                self.params.subfolder_record_cache.get(folder_uid, set()) or set()
            )
        return record_uids

    def _folder_path(self, folder_uid):
        """Build a human-readable path by following parent UIDs upward.

        The returned path is presentation metadata only; Keeper operations
        continue to use the original UID.
        """
        names = []
        uid = folder_uid

        while uid in self.params.folder_cache:
            folder = self.params.folder_cache[uid]
            name = getattr(folder, "name", "") or uid
            names.append(name)
            uid = getattr(folder, "parent_uid", None)
            if not uid:
                break

        names.reverse()
        return "/".join(names)

    def _load_folder_list(self):
        """Rebuild the group selector from the live synchronised folder cache.

        Only folders whose selected subtree contains records are shown. Full
        paths disambiguate same-named folders. If even the full label collides, a
        short UID suffix provides a deterministic UI distinction.

        Record counts include descendants because preview/export also include
        the complete selected subtree.
        """
        choices = []
        mapping = {}

        for uid, folder in self.params.folder_cache.items():
            if not uid or not folder:
                continue

            count = len(self._record_uids_for_folder(uid))
            if count <= 0:
                continue

            path = self._folder_path(uid)
            label = f"{path}  ({count})"

            if label in mapping:
                # Full-path collisions should be unusual, but the UID suffix
                # guarantees the display map remains one-to-one.
                label = f"{label}  [{uid[:8]}]"

            mapping[label] = uid
            choices.append(label)

        choices.sort(key=lambda value: value.casefold())
        self.folder_by_label = mapping
        self.group_box["values"] = choices

        if choices:
            self.group_box.config(state="readonly")
            self.export_btn.config(state="normal")

            # Year 3 is only an initial-selection convenience. Available groups
            # themselves are always discovered dynamically from Keeper.
            preferred_index = 0
            for index, label in enumerate(choices):
                plain = re.sub(r"\s+\(\d+\)(?:\s+\[[^\]]+\])?$", "", label)
                if plain.endswith("/Year 3") or plain == "Year 3":
                    preferred_index = index
                    break

            self.group_box.current(preferred_index)
            self.on_group_selected()
        else:
            self.group_box.config(state="disabled")
            self.export_btn.config(state="disabled")
            self.folder_info.config(text="No Keeper folders containing records were found.")

    def _records_for_selected_folder(self):
        """Project Keeper records onto Student / Email / Password rows.

        Direct API reads are intentional: Keeper's CSV export schema varies by
        record type/version, whereas Commander exposes the legacy-compatible
        title/login/password projection used here.

        A failure to read one record is isolated rather than aborting the whole
        group. This preserves useful output while keeping the fault boundary at
        record granularity.
        """
        if not self.params:
            raise RuntimeError("Not connected to Keeper.")

        label = self.group_var.get()
        uid = self.folder_by_label.get(label)
        if not uid:
            raise RuntimeError("Choose a Keeper folder first.")

        rows = []

        for record_uid in self._record_uids_for_folder(uid):
            try:
                record = self.k_api.get_record(self.params, record_uid)
            except Exception:
                record = None

            if not record:
                continue

            student = (getattr(record, "title", "") or "").strip()
            email = (getattr(record, "login", "") or "").strip()
            password = getattr(record, "password", "") or ""

            # Keep partially-complete records visible. Requiring all fields
            # would hide data-quality problems rather than exposing empty cells.
            if student or email or password:
                rows.append({
                    "Student": student,
                    "Email": email,
                    "Password": password,
                })

        rows.sort(key=lambda row: row["Student"].casefold())
        return rows

    def on_group_selected(self, event=None):
        """Refresh the preview after user or programmatic folder selection."""
        try:
            self.rows = self._records_for_selected_folder()
            self._populate_preview()

            label = self.group_var.get()
            folder_name = re.sub(r"\s+\(\d+\)(?:\s+\[[^\]]+\])?$", "", label)
            self.folder_info.config(
                text=f"{folder_name} • {len(self.rows)} exportable records"
            )
            self._set_status(f"Loaded {len(self.rows)} records from {folder_name}", tone="success")

        except Exception as exc:
            self.rows = []
            self._populate_preview()
            self.folder_info.config(text=str(exc))
            self.metric_count.config(text="—")

    def _populate_preview(self):
        """Render the preview using the current search and privacy controls.

        Search and password masking are presentation-only. ``self.rows`` remains
        the complete authoritative projection for the selected folder, and export
        always re-reads Keeper independently of these visual filters.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        query = self.search_var.get().strip().casefold()
        hide_passwords = self.hide_passwords_var.get()

        if query:
            self.filtered_rows = [
                row for row in self.rows
                if query in row["Student"].casefold()
                or query in row["Email"].casefold()
                or query in row["Password"].casefold()
            ]
        else:
            self.filtered_rows = list(self.rows)

        for row in self.filtered_rows:
            password = "••••••••" if hide_passwords and row["Password"] else row["Password"]
            self.tree.insert(
                "",
                "end",
                values=(row["Student"], row["Email"], password)
            )

        total = len(self.rows)
        visible = len(self.filtered_rows)

        if query:
            self.preview_count.config(text=f"{visible} of {total} records shown")
        else:
            self.preview_count.config(text=f"{total} records")

        self.metric_count.config(text=str(total) if total else "0")

    def export_selected(self):
        """Write the currently selected group to a clean plaintext CSV.

        Records are re-read at save time rather than serialising the last
        preview blindly. ``utf-8-sig`` is intentional for predictable Excel
        recognition on Windows.
        """
        try:
            rows = self._records_for_selected_folder()

            if not rows:
                raise RuntimeError(
                    "The selected folder contains no exportable credential records."
                )

            label = self.group_var.get()
            folder_name = re.sub(r"\s+\(\d+\)(?:\s+\[[^\]]+\])?$", "", label)
            base_name = safe_filename(folder_name.replace("/", " - "))

            path = filedialog.asksaveasfilename(
                title=f"Export {folder_name}",
                initialdir=os.path.expanduser("~"),
                initialfile=f"{base_name}-Credentials.csv",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                parent=self
            )

            if not path:
                self._set_status("Export cancelled", tone="muted")
                return

            # newline="" lets csv.DictWriter control line termination and avoids
            # blank-line artefacts on Windows.
            with open(path, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["Student", "Email", "Password"]
                )
                writer.writeheader()
                writer.writerows(rows)

            self.rows = rows
            self._populate_preview()

            self._set_status(f"Exported {len(rows)} records", tone="success")

            messagebox.showinfo(
                APP_TITLE,
                f"Export complete.\n\n{len(rows)} records written to:\n{path}",
                parent=self
            )

        except Exception as exc:
            self._set_status("Export failed", tone="danger")
            messagebox.showerror(
                APP_TITLE,
                "Could not export the selected group.\n\n" + str(exc),
                parent=self
            )
