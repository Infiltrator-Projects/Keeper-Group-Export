"""Application-local constants and pure helper functions.

This module is intentionally Python-only. It is not an embedded copy or binding
of Infiltratr Common; the native C11 library currently exposes no supported
Python consumer interface that would improve this utility.
"""

import re

APP_TITLE = "Keeper Group Export"
APP_VERSION = "3.8"
APP_SUBTITLE = "Credential Export Utility"
PROGRAMMERS = ("Shannon Smith", "Carlo Cunanan")
KEEPER_COMMANDER_VERSION = "18.1.2"

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
    text = re.sub(r'[<>:"/\\\\|?*]+', "-", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or "Keeper-Group"


def build_folder_record_index(folder_cache, direct_record_cache):
    """Build ``folder UID -> all record UIDs in that folder subtree``.

    Keeper supplies direct record membership separately from the folder tree.
    Building the transitive index once after each vault sync avoids recursively
    re-walking the same descendants for every folder displayed in the selector.

    The defensive ``visiting`` guard bounds malformed cyclic folder data. A
    normal Keeper folder graph is acyclic.
    """
    memo = {}
    visiting = set()

    def collect(uid):
        cached = memo.get(uid)
        if cached is not None:
            return cached

        records = set(direct_record_cache.get(uid, ()) or ())
        if uid in visiting:
            return frozenset(records)

        visiting.add(uid)
        try:
            folder = folder_cache.get(uid)
            if folder:
                for child_uid in getattr(folder, "subfolders", ()) or ():
                    records.update(collect(child_uid))
        finally:
            visiting.discard(uid)

        result = frozenset(records)
        memo[uid] = result
        return result

    for uid in set(folder_cache) | set(direct_record_cache):
        collect(uid)

    return memo
