# Keeper Group Export

Keeper Group Export is a Windows GUI utility for exporting credential records from a selected live Keeper folder to a clean CSV containing only **Student**, **Email**, and **Password**.

## Run

Clone or download the repository, keep the files together, then double-click:

`Start Keeper Group Export.vbs`

Normal launches use an already-prepared Python runtime directly. On a clean PC, the PowerShell bootstrap can prepare Python 3.13 x64 and Keeper Commander 18.1.2 before starting the GUI.

## Features

- Keeper login, device approval and 2FA through Keeper Commander's `LoginUi` flow.
- Dynamic discovery of live Keeper folders; no school-year or organisational folders are hard-coded.
- Student / Email / Password preview.
- Live preview search.
- Preview-only password masking.
- Refresh Vault without forcing a new login.
- UTF-8 CSV export for Microsoft Excel.
- Remembers the last successful Keeper username locally on that PC only.
- Professional About screen and programmer credits.

## Source layout

The thin entry point is `Keeper-Group-Export-v3.8.pyw`.

The application is split into focused modules under `keeper_group_export/` for maintainability:

- `app.py` — application composition and local non-secret settings.
- `auth_runtime.py` — deferred Keeper import/config handling.
- `auth_present.py` — login presentation.
- `auth_flow.py` — Keeper device approval, 2FA and password flow.
- `ui_styles.py` / `ui_layout.py` / `ui_helpers.py` / `ui_actions.py` — desktop UI.
- `vault.py` — folder traversal, preview and CSV export.
- `common.py` — shared constants and utilities.

## Privacy / security

**No Keeper username, email address, password, token, or vault data is hard-coded or shipped in this repository.**

A fresh installation starts with a blank username unless that PC already has a locally remembered username from a previous successful login.

The remembered username is stored only under:

`%LOCALAPPDATA%\KeeperGroupExport\settings.json`

That local file is outside the repository and is also excluded by `.gitignore` as a defence-in-depth measure.

The application does not deliberately persist the Keeper master password. Exported CSV files do contain plaintext passwords by design, so they must be treated as sensitive credential material.

## Keyboard shortcuts

- `Ctrl+F` — focus preview search
- `F5` — refresh connected vault
- `Ctrl+E` — export selected folder
- `F1` — About

## Programmers

- Shannon Smith
- Carlo Cunanan

## Technology

- Python 3.13 x64
- Tkinter
- Keeper Commander 18.1.2
- PowerShell / VBScript bootstrap and launcher

Current version: **3.8**

Keeper and Keeper Commander are products of Keeper Security, Inc. This is an independent utility and not an official Keeper Security product.
