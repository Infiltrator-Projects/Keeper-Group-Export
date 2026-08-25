"""Keeper Group Export ui helpers module."""

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

class UIHelpersMixin:
    def _set_status(self, text, *, tone="muted"):
        """Update the footer and vault status indicator consistently."""
        self.footer_status.config(text=text)

        colours = {
            "muted": C_MUTED,
            "success": C_SUCCESS,
            "warning": C_WARNING,
            "danger": C_DANGER,
            "info": C_INFO,
        }
        colour = colours.get(tone, C_MUTED)

        if hasattr(self, "status_dot"):
            self.status_dot.itemconfigure("dot", fill=colour, outline=colour)

    def _focus_search(self):
        """Move keyboard focus to the preview filter."""
        if hasattr(self, "search_entry"):
            self.search_entry.focus_set()
            self.search_entry.select_range(0, "end")

    def _shortcut_export(self):
        """Execute export only when the export control is currently available."""
        try:
            if str(self.export_btn["state"]) != "disabled":
                self.export_selected()
        except Exception:
            pass

    def _shortcut_refresh(self):
        """Refresh the connected vault only when a session exists."""
        if self.params:
            self.refresh_vault()
