"""Application-local constants and pure helper functions.

This module is intentionally Python-only. It is not an embedded copy or binding
of Infiltratr Common; the native C11 library currently exposes no supported
Python consumer interface that would improve this utility.

Graphical presentation follows the canonical Infiltrator Design v1 contract in
Infiltrator-Libraries. MBLINK is the reference implementation; Keeper keeps its
own yellow product accent while sharing the graphite/silver foundation and MB
Corpo typography roles.
"""

import re

APP_TITLE = "Keeper Group Export"
APP_VERSION = "1.0.1"
APP_SUBTITLE = "Credential Export Utility"
PROGRAMMERS = ("Shannon Smith", "Carlo Cunanan")
KEEPER_COMMANDER_VERSION = "18.1.2"

# Infiltrator Design v1 typography. Tk falls back to its platform font mapper
# automatically if these private/local faces are not installed.
FONT_UI = "MB Corpo S Title WEB"
FONT_BRAND = "MB Corpo A Title Cond WEB"
FONT_UI_FALLBACK = "Segoe UI"

# Infiltrator Design v1 graphite/silver structural palette. Keeper's yellow
# accent remains product-owned.
C_BG = "#050608"
C_PANEL = "#101318"
C_PANEL_2 = "#171b20"
C_INPUT = "#0e1115"
C_BORDER = "#353a40"
C_TEXT = "#e8ecef"
C_MUTED = "#aeb6bd"
C_ACCENT = "#ffcc00"
C_ACCENT_HOVER = "#ffd633"
C_DANGER = "#c96b6b"
C_SELECTED = "#2b3137"
C_SIDEBAR = "#050608"
C_CARD = "#171b20"
C_CARD_ALT = "#0d1014"
C_SUCCESS = "#63ab7c"
C_WARNING = "#d19e47"
C_INFO = "#7fa7c9"


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
