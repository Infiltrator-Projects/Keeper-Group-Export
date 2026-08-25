"""Primary Keeper Group Export window layout."""

import tkinter as tk
from tkinter import ttk

from .common import (
    APP_TITLE,
    APP_VERSION,
    C_ACCENT,
    C_BG,
    C_BORDER,
    C_CARD,
    C_INPUT,
    C_MUTED,
    C_SIDEBAR,
    C_TEXT,
    C_WARNING,
)


class UILayoutMixin:
    def _build_ui(self):
        """Construct the primary application shell.

        The visual hierarchy separates global navigation, vault state, folder
        selection and the record workspace. Authentication/data loading remains
        outside this method so the window can paint immediately.
        """
        outer = tk.Frame(self, bg=C_BG)
        outer.pack(fill="both", expand=True)

        # Sidebar -----------------------------------------------------------
        sidebar = tk.Frame(outer, bg=C_SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=C_SIDEBAR)
        brand.pack(fill="x", padx=20, pady=(24, 18))

        badge = tk.Canvas(brand, width=38, height=38, bg=C_SIDEBAR, highlightthickness=0)
        badge.create_oval(2, 2, 36, 36, fill=C_ACCENT, outline=C_ACCENT)
        badge.create_text(19, 19, text="K", fill="#111111", font=("Segoe UI Black", 16))
        badge.pack(side="left")

        brand_text = tk.Frame(brand, bg=C_SIDEBAR)
        brand_text.pack(side="left", padx=(10, 0))
        tk.Label(
            brand_text,
            text="KEEPER",
            bg=C_SIDEBAR,
            fg=C_TEXT,
            font=("Segoe UI Semibold", 14),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="GROUP EXPORT",
            bg=C_SIDEBAR,
            fg="#8f8f8f",
            font=("Segoe UI", 7),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            sidebar,
            text="WORKSPACE",
            bg=C_SIDEBAR,
            fg="#707070",
            font=("Segoe UI Semibold", 7),
            anchor="w",
        ).pack(fill="x", padx=22, pady=(8, 6))

        export_nav = tk.Frame(sidebar, bg="#2c2c2c", height=42)
        export_nav.pack(fill="x", padx=10)
        export_nav.pack_propagate(False)
        tk.Label(
            export_nav,
            text="  ▣  Group Export",
            bg="#2c2c2c",
            fg=C_TEXT,
            font=("Segoe UI Semibold", 9),
            anchor="w",
        ).pack(fill="both", expand=True)

        tk.Button(
            sidebar,
            text="  ⓘ  About",
            command=self.show_about,
            bg=C_SIDEBAR,
            fg=C_MUTED,
            activebackground="#242424",
            activeforeground=C_TEXT,
            relief="flat",
            bd=0,
            font=("Segoe UI", 9),
            anchor="w",
            padx=11,
            pady=10,
        ).pack(fill="x", padx=10, pady=(4, 0))

        tk.Frame(sidebar, bg=C_SIDEBAR).pack(fill="both", expand=True)

        footer = tk.Frame(sidebar, bg=C_SIDEBAR)
        footer.pack(fill="x", padx=20, pady=18)
        tk.Label(
            footer,
            text=f"Version {APP_VERSION}",
            bg=C_SIDEBAR,
            fg="#727272",
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            footer,
            text="Shannon Smith • Carlo Cunanan",
            bg=C_SIDEBAR,
            fg="#727272",
            font=("Segoe UI", 7),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Main content ------------------------------------------------------
        self.main = tk.Frame(outer, bg=C_BG)
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=C_BG)
        header.pack(fill="x", padx=28, pady=(24, 16))

        title_block = tk.Frame(header, bg=C_BG)
        title_block.pack(side="left")
        tk.Label(
            title_block,
            text=APP_TITLE,
            bg=C_BG,
            fg=C_TEXT,
            font=("Segoe UI Semibold", 21),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Export selected Keeper folders to a clean, parent-ready credential CSV.",
            bg=C_BG,
            fg=C_MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        self.account_badge = tk.Label(
            header,
            text="Not connected",
            bg="#202020",
            fg=C_MUTED,
            font=("Segoe UI Semibold", 8),
            padx=12,
            pady=7,
        )
        self.account_badge.pack(side="right", padx=(10, 0))

        tk.Frame(self.main, bg="#313131", height=1).pack(
            fill="x", padx=28, pady=(0, 18)
        )

        content = tk.Frame(self.main, bg=C_BG)
        content.pack(fill="both", expand=True, padx=28)

        # Connection status ------------------------------------------------
        status_card = tk.Frame(
            content,
            bg=C_CARD,
            highlightbackground="#353535",
            highlightthickness=1,
        )
        status_card.pack(fill="x", pady=(0, 12))
        status_inner = tk.Frame(status_card, bg=C_CARD)
        status_inner.pack(fill="x", padx=18, pady=15)

        status_left = tk.Frame(status_inner, bg=C_CARD)
        status_left.pack(side="left", fill="x", expand=True)
        status_title = tk.Frame(status_left, bg=C_CARD)
        status_title.pack(anchor="w")

        self.status_dot = tk.Canvas(
            status_title, width=12, height=12, bg=C_CARD, highlightthickness=0
        )
        self.status_dot.create_oval(
            2, 2, 10, 10, fill=C_WARNING, outline=C_WARNING, tags="dot"
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        tk.Label(
            status_title,
            text="Vault connection",
            bg=C_CARD,
            fg=C_TEXT,
            font=("Segoe UI Semibold", 10),
        ).pack(side="left")

        self.conn_status = tk.Label(
            status_left,
            text="Preparing Keeper library…",
            bg=C_CARD,
            fg=C_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.conn_status.pack(anchor="w", pady=(5, 0))

        actions = tk.Frame(status_inner, bg=C_CARD)
        actions.pack(side="right")
        self.refresh_btn = ttk.Button(
            actions,
            text="Refresh Vault",
            style="Toolbar.TButton",
            command=self.refresh_vault,
            state="disabled",
        )
        self.refresh_btn.pack(side="left")
        self.reload_btn = ttk.Button(
            actions,
            text="Reconnect",
            style="Toolbar.TButton",
            command=self.show_login_screen,
            state="disabled",
        )
        self.reload_btn.pack(side="left", padx=(8, 0))

        # Folder selection -------------------------------------------------
        group_card = tk.Frame(
            content,
            bg=C_CARD,
            highlightbackground="#353535",
            highlightthickness=1,
        )
        group_card.pack(fill="x", pady=(0, 12))
        group_inner = tk.Frame(group_card, bg=C_CARD)
        group_inner.pack(fill="x", padx=18, pady=15)

        group_left = tk.Frame(group_inner, bg=C_CARD)
        group_left.pack(side="left", fill="x", expand=True)
        tk.Label(
            group_left,
            text="Keeper folder",
            bg=C_CARD,
            fg=C_TEXT,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            group_left,
            text="Choose a live folder from the connected vault.",
            bg=C_CARD,
            fg=C_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(anchor="w", pady=(2, 8))

        picker_row = tk.Frame(group_left, bg=C_CARD)
        picker_row.pack(fill="x")
        self.group_var = tk.StringVar()
        self.group_box = ttk.Combobox(
            picker_row,
            textvariable=self.group_var,
            state="disabled",
            style="Keeper.TCombobox",
        )
        self.group_box.pack(side="left", fill="x", expand=True)
        self.group_box.bind("<<ComboboxSelected>>", self.on_group_selected)

        self.export_btn = ttk.Button(
            picker_row,
            text="Export CSV",
            style="Accent.TButton",
            command=self.export_selected,
            state="disabled",
        )
        self.export_btn.pack(side="left", padx=(10, 0))

        self.folder_info = tk.Label(
            group_left,
            text="Connect to Keeper to load available folders.",
            bg=C_CARD,
            fg=C_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.folder_info.pack(anchor="w", pady=(7, 0))

        metric = tk.Frame(group_inner, bg=C_CARD, width=105)
        metric.pack(side="right", padx=(20, 0))
        metric.pack_propagate(False)
        self.metric_count = tk.Label(
            metric,
            text="—",
            bg=C_CARD,
            fg=C_ACCENT,
            font=("Segoe UI Semibold", 20),
        )
        self.metric_count.pack(anchor="e")
        tk.Label(
            metric,
            text="records",
            bg=C_CARD,
            fg=C_MUTED,
            font=("Segoe UI", 8),
        ).pack(anchor="e")

        # Preview ----------------------------------------------------------
        preview = tk.Frame(
            content,
            bg=C_CARD,
            highlightbackground="#353535",
            highlightthickness=1,
        )
        preview.pack(fill="both", expand=True, pady=(0, 12))

        preview_header = tk.Frame(preview, bg=C_CARD)
        preview_header.pack(fill="x", padx=16, pady=(13, 10))
        preview_title = tk.Frame(preview_header, bg=C_CARD)
        preview_title.pack(side="left")
        tk.Label(
            preview_title,
            text="Credential preview",
            bg=C_CARD,
            fg=C_TEXT,
            font=("Segoe UI Semibold", 10),
        ).pack(anchor="w")
        self.preview_count = tk.Label(
            preview_title,
            text="",
            bg=C_CARD,
            fg=C_MUTED,
            font=("Segoe UI", 8),
        )
        self.preview_count.pack(anchor="w", pady=(2, 0))

        tools = tk.Frame(preview_header, bg=C_CARD)
        tools.pack(side="right")
        tk.Label(
            tools, text="Search", bg=C_CARD, fg=C_MUTED, font=("Segoe UI", 8)
        ).pack(side="left", padx=(0, 6))
        self.search_entry = tk.Entry(
            tools,
            textvariable=self.search_var,
            bg=C_INPUT,
            fg=C_TEXT,
            insertbackground=C_TEXT,
            relief="flat",
            highlightthickness=1,
            highlightbackground=C_BORDER,
            highlightcolor=C_ACCENT,
            font=("Segoe UI", 9),
            width=24,
        )
        self.search_entry.pack(side="left")
        self.hide_passwords_check = tk.Checkbutton(
            tools,
            text="Hide passwords",
            variable=self.hide_passwords_var,
            command=self._populate_preview,
            bg=C_CARD,
            fg=C_MUTED,
            activebackground=C_CARD,
            activeforeground=C_TEXT,
            selectcolor=C_INPUT,
            font=("Segoe UI", 8),
            padx=10,
        )
        self.hide_passwords_check.pack(side="left")

        table_frame = tk.Frame(preview, bg=C_CARD)
        table_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))
        self.tree = ttk.Treeview(
            table_frame,
            columns=("student", "email", "password"),
            show="headings",
            style="Keeper.Treeview",
        )
        self.tree.heading("student", text="Student")
        self.tree.heading("email", text="Email")
        self.tree.heading("password", text="Password")
        self.tree.column("student", width=270, minwidth=170, anchor="w")
        self.tree.column("email", width=390, minwidth=240, anchor="w")
        self.tree.column("password", width=220, minwidth=160, anchor="w")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Bottom status ----------------------------------------------------
        bottom = tk.Frame(self.main, bg=C_BG)
        bottom.pack(fill="x", padx=28, pady=(0, 14))
        self.footer_status = tk.Label(
            bottom,
            text="Ready",
            bg=C_BG,
            fg="#858585",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.footer_status.pack(side="left")
        tk.Label(
            bottom,
            text="Ctrl+F Search   •   F5 Refresh   •   Ctrl+E Export   •   F1 About",
            bg=C_BG,
            fg="#6f6f6f",
            font=("Segoe UI", 8),
            anchor="e",
        ).pack(side="right")

        self.login_overlay = None

        # Search affects preview only; export always remains the complete folder.
        self.search_var.trace_add("write", lambda *_args: self._populate_preview())
        self.bind_all("<Control-f>", lambda _event: self._focus_search())
        self.bind_all("<Control-e>", lambda _event: self._shortcut_export())
        self.bind_all("<F5>", lambda _event: self._shortcut_refresh())
        self.bind_all("<F1>", lambda _event: self.show_about())
