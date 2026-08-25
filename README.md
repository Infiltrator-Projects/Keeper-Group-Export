# Keeper Group Export

Keeper Group Export is a Windows GUI utility for exporting credential records
from a selected live Keeper folder to a clean CSV containing only **Student**,
**Email**, and **Password**.

## Download

The current public download remains GitHub Release **v3.8.0** while `main` is
being hardened for the forthcoming 1.0 release.

## Run

Extract the package, keep the files together, then double-click:

`Start Keeper Group Export.vbs`

Normal launches use a previously verified Python runtime directly. A clean or
newly-hardened installation runs the PowerShell bootstrap once to locate/install
Python 3.13 x64, enforce the pinned Keeper Commander dependency, verify the
runtime, and cache the verified launcher for subsequent fast starts.

## Features

- Keeper login, device approval and 2FA through Keeper Commander's `LoginUi`.
- Dynamic discovery of live Keeper folders; no organisational folders are hard-coded.
- Student / Email / Password preview and CSV export.
- Live preview search and preview-only password masking.
- Refresh Vault without forcing a new login.
- Remembers the last successful Keeper username locally on that PC only.
- Single-pass folder/record indexing after each vault sync.
- Professional About screen and programmer credits.

## Authentication support

The application supports Keeper's login/password flow plus the device-approval
and 2FA channels implemented in the GUI, including authenticator codes, SMS,
Duo, RSA SecurID, Keeper DNA and backup codes where Keeper exposes them.

**WebAuthn/security-key-only authentication is not currently driven by this
Tkinter utility.** If an account exposes only that factor, the program reports
the limitation and cancels the login rather than bypassing or weakening it.

## Source layout

The thin entry point is `Keeper-Group-Export-v3.8.pyw`. Focused modules live
under `keeper_group_export/`:

- `app.py` — application composition and local non-secret settings.
- `auth_runtime.py` — deferred Keeper import/config handling.
- `auth_present.py` — login and authentication-choice presentation.
- `auth_flow.py` — Keeper device approval, 2FA and password flow.
- `ui_styles.py` / `ui_layout.py` / `ui_helpers.py` / `ui_actions.py` — desktop UI.
- `vault.py` — indexed folder discovery, preview and CSV export.
- `common.py` — application-local constants and pure helpers.

`requirements.txt` is the pinned runtime dependency source of truth. Windows CI
compiles/imports the modules, runs pure unit tests, rejects wildcard local
imports, and parses the PowerShell bootstrap.

## Privacy / security

**No Keeper username, email address, password, token, or vault data is hard-coded
or shipped in this repository.**

A fresh installation starts with a blank username unless that PC already has a
locally remembered username from a previous successful login. The remembered
username is stored only under:

`%LOCALAPPDATA%\KeeperGroupExport\settings.json`

The application does not deliberately persist the Keeper master password.
Exported CSV files contain plaintext passwords by design, so they must be treated
as sensitive credential material.

If any Keeper record in the selected folder cannot be read, export is stopped
rather than silently writing an incomplete credential list.

## Infiltratr Common

Keeper Group Export is **not currently linked to Infiltratr Common**. Common
1.14 is a native C11 library and currently has no supported Python binding for
the facilities this application needs. Adding a private FFI layer solely to
claim Common linkage would increase startup time, packaging complexity and
failure surface without removing meaningful duplicated logic.

This is deliberate. If Common gains a supported Python consumer interface for a
genuinely shared contract used here, Keeper Group Export should pin and consume
that interface rather than maintaining a private fork.

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

Current development version: **3.8**  
Current published release: **v3.8.0**

Keeper and Keeper Commander are products of Keeper Security, Inc. This is an
independent utility and not an official Keeper Security product.
