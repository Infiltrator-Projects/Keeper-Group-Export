"""Keeper folder indexing, preview projection and CSV export."""

import csv
import os
import re
from tkinter import filedialog, messagebox

from .common import APP_TITLE, build_folder_record_index, safe_filename


class VaultMixin:
    def _rebuild_folder_record_index(self):
        """Build the transitive folder->record index once for the current sync."""
        if not self.params:
            self.folder_record_index = {}
            return

        self.folder_record_index = build_folder_record_index(
            self.params.folder_cache,
            self.params.subfolder_record_cache,
        )

    def _record_uids_for_folder(self, root_uid):
        """Return the de-duplicated record UIDs in one indexed folder subtree."""
        if not self.folder_record_index:
            self._rebuild_folder_record_index()
        return set(self.folder_record_index.get(root_uid, ()))

    def _folder_path(self, folder_uid):
        """Build a human-readable full path by following parent UIDs upward.

        The path is display metadata only. A defensive ``seen`` set prevents
        malformed cyclic parent references from hanging the GUI.
        """
        names = []
        seen = set()
        uid = folder_uid

        while uid and uid not in seen and uid in self.params.folder_cache:
            seen.add(uid)
            folder = self.params.folder_cache[uid]
            names.append(getattr(folder, "name", "") or uid)
            uid = getattr(folder, "parent_uid", None)

        names.reverse()
        return "/".join(names)

    def _load_folder_list(self):
        """Rebuild the selector and its index from the current Keeper caches.

        The subtree record index is computed once here and then reused for every
        folder count, selection, preview and export until the next vault sync.
        """
        self._rebuild_folder_record_index()

        choices = []
        mapping = {}

        for uid, folder in self.params.folder_cache.items():
            if not uid or not folder:
                continue

            count = len(self.folder_record_index.get(uid, ()))
            if count <= 0:
                continue

            path = self._folder_path(uid)
            label = f"{path}  ({count})"

            if label in mapping:
                label = f"{label}  [{uid[:8]}]"

            mapping[label] = uid
            choices.append(label)

        choices.sort(key=str.casefold)
        self.folder_by_label = mapping
        self.group_box["values"] = choices

        if choices:
            self.group_box.config(state="readonly")
            self.export_btn.config(state="normal")

            # Year 3 remains only an initial-selection convenience. Folder
            # availability itself is always derived from the live vault.
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
        """Project the selected folder onto Student / Email / Password rows.

        Direct Keeper API reads avoid dependence on Keeper's variable CSV schema.
        A record-read failure aborts the projection rather than silently producing
        an incomplete credential list.
        """
        if not self.params:
            raise RuntimeError("Not connected to Keeper.")

        label = self.group_var.get()
        folder_uid = self.folder_by_label.get(label)
        if not folder_uid:
            raise RuntimeError("Choose a Keeper folder first.")

        rows = []
        failures = []

        for record_uid in self._record_uids_for_folder(folder_uid):
            try:
                record = self.k_api.get_record(self.params, record_uid)
            except Exception as exc:
                failures.append((record_uid, exc))
                continue

            if record is None:
                failures.append((record_uid, RuntimeError("Keeper returned no record")))
                continue

            student = (getattr(record, "title", "") or "").strip()
            email = (getattr(record, "login", "") or "").strip()
            password = getattr(record, "password", "") or ""

            # Preserve partially-complete records so data-quality issues remain
            # visible instead of being silently dropped.
            if student or email or password:
                rows.append({
                    "Student": student,
                    "Email": email,
                    "Password": password,
                })

        if failures:
            raise RuntimeError(
                f"Keeper could not read {len(failures)} record(s) in the selected "
                "folder. Refresh the vault and retry; export was not allowed to "
                "continue with an incomplete credential set."
            )

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
            self._set_status(
                f"Loaded {len(self.rows)} records from {folder_name}",
                tone="success",
            )

        except Exception as exc:
            self.rows = []
            self._populate_preview()
            self.folder_info.config(text=str(exc))
            self.metric_count.config(text="—")
            self._set_status("Could not load selected folder", tone="danger")

    def _populate_preview(self):
        """Render preview rows using the current search/privacy controls.

        Search and password masking are presentation-only. ``self.rows`` remains
        the complete current projection and export re-reads Keeper independently.
        """
        for item in self.tree.get_children():
            self.tree.delete(item)

        query = self.search_var.get().strip().casefold()
        hide_passwords = self.hide_passwords_var.get()

        if query:
            self.filtered_rows = [
                row
                for row in self.rows
                if query in row["Student"].casefold()
                or query in row["Email"].casefold()
                or query in row["Password"].casefold()
            ]
        else:
            self.filtered_rows = list(self.rows)

        for row in self.filtered_rows:
            password = (
                "••••••••"
                if hide_passwords and row["Password"]
                else row["Password"]
            )
            self.tree.insert(
                "",
                "end",
                values=(row["Student"], row["Email"], password),
            )

        total = len(self.rows)
        visible = len(self.filtered_rows)

        if query:
            self.preview_count.config(text=f"{visible} of {total} records shown")
        else:
            self.preview_count.config(text=f"{total} records")

        self.metric_count.config(text=str(total) if total else "0")

    def export_selected(self):
        """Write the currently selected group to a clean plaintext CSV."""
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
                parent=self,
            )

            if not path:
                self._set_status("Export cancelled", tone="muted")
                return

            # newline="" delegates newline handling to csv.DictWriter and avoids
            # blank-line artefacts on Windows.
            with open(path, "w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["Student", "Email", "Password"],
                )
                writer.writeheader()
                writer.writerows(rows)

            self.rows = rows
            self._populate_preview()
            self._set_status(f"Exported {len(rows)} records", tone="success")

            messagebox.showinfo(
                APP_TITLE,
                f"Export complete.\n\n{len(rows)} records written to:\n{path}",
                parent=self,
            )

        except Exception as exc:
            self._set_status("Export failed", tone="danger")
            messagebox.showerror(
                APP_TITLE,
                "Could not export the selected group.\n\n" + str(exc),
                parent=self,
            )
