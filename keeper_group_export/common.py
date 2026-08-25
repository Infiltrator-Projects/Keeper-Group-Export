"""Shared identity, presentation constants and utility functions."""

import re

APP_TITLE = "Keeper Group Export"
APP_VERSION = "3.8"
APP_SUBTITLE = "Credential Export Utility"
PROGRAMMERS = ("Shannon Smith", "Carlo Cunanan")

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
    """Return a Windows-safe filename stem for an exported Keeper folder."""
    text = re.sub(r'[<>:"/\\|?*]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "Keeper-Group"
