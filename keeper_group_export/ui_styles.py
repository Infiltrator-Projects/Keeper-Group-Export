"""ttk style definitions for the Keeper-inspired desktop presentation."""

from tkinter import ttk

from .common import (
    C_ACCENT,
    C_ACCENT_HOVER,
    C_BG,
    C_BORDER,
    C_CARD,
    C_CARD_ALT,
    C_INPUT,
    C_MUTED,
    C_PANEL,
    C_PANEL_2,
    C_SELECTED,
    C_TEXT,
)


class UIStylesMixin:
    def _build_styles(self):
        """Configure the deterministic Keeper-inspired ttk presentation."""
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            # Theme availability is cosmetic; keep the active ttk theme.
            pass

        style.configure("Keeper.TFrame", background=C_BG)
        style.configure("Panel.TFrame", background=C_PANEL)
        style.configure("Panel2.TFrame", background=C_PANEL_2)
        style.configure("Keeper.TLabel", background=C_BG, foreground=C_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=C_BG, foreground=C_TEXT, font=("Segoe UI Semibold", 19))
        style.configure("Section.TLabel", background=C_PANEL, foreground=C_TEXT, font=("Segoe UI Semibold", 11))
        style.configure("Muted.TLabel", background=C_BG, foreground=C_MUTED, font=("Segoe UI", 9))
        style.configure("PanelMuted.TLabel", background=C_PANEL, foreground=C_MUTED, font=("Segoe UI", 9))

        style.configure(
            "Accent.TButton",
            background=C_ACCENT,
            foreground="#111111",
            bordercolor=C_ACCENT,
            lightcolor=C_ACCENT,
            darkcolor=C_ACCENT,
            font=("Segoe UI Semibold", 10),
            padding=(14, 8),
        )
        style.map(
            "Accent.TButton",
            background=[("active", C_ACCENT_HOVER), ("disabled", "#6a5d1c")],
            foreground=[("disabled", "#b7ad84")],
        )

        style.configure(
            "Dark.TButton",
            background=C_INPUT,
            foreground=C_TEXT,
            bordercolor=C_BORDER,
            font=("Segoe UI", 10),
            padding=(12, 8),
        )
        style.map(
            "Dark.TButton",
            background=[("active", "#474747"), ("disabled", "#2d2d2d")],
            foreground=[("disabled", "#777777")],
        )

        style.configure(
            "Keeper.TCombobox",
            fieldbackground=C_INPUT,
            background=C_INPUT,
            foreground=C_TEXT,
            arrowcolor=C_TEXT,
            bordercolor=C_BORDER,
            lightcolor=C_BORDER,
            darkcolor=C_BORDER,
            padding=6,
        )
        style.map(
            "Keeper.TCombobox",
            fieldbackground=[("readonly", C_INPUT)],
            foreground=[("readonly", C_TEXT)],
            selectbackground=[("readonly", C_INPUT)],
            selectforeground=[("readonly", C_TEXT)],
        )

        style.configure(
            "Keeper.Treeview",
            background=C_PANEL,
            fieldbackground=C_PANEL,
            foreground=C_TEXT,
            rowheight=32,
            bordercolor=C_BORDER,
            lightcolor=C_PANEL,
            darkcolor=C_PANEL,
        )
        style.configure(
            "Keeper.Treeview.Heading",
            background=C_PANEL_2,
            foreground=C_TEXT,
            font=("Segoe UI Semibold", 10),
            relief="flat",
        )
        style.map(
            "Keeper.Treeview",
            background=[("selected", C_SELECTED)],
            foreground=[("selected", C_TEXT)],
        )

        style.configure(
            "CardTitle.TLabel",
            background=C_CARD,
            foreground=C_TEXT,
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "CardMuted.TLabel",
            background=C_CARD,
            foreground=C_MUTED,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Metric.TLabel",
            background=C_CARD,
            foreground=C_ACCENT,
            font=("Segoe UI Semibold", 18),
        )
        style.configure(
            "Toolbar.TButton",
            background=C_CARD_ALT,
            foreground=C_TEXT,
            bordercolor=C_BORDER,
            font=("Segoe UI", 9),
            padding=(10, 6),
        )
        style.map(
            "Toolbar.TButton",
            background=[("active", "#353535"), ("disabled", C_CARD)],
            foreground=[("disabled", "#707070")],
        )
