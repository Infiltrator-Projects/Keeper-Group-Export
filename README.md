# Keeper Group Export

Keeper Group Export is a Windows GUI utility for exporting credential records from a selected live Keeper folder to a clean CSV containing only **Student**, **Email**, and **Password**.

## Download

The current stable release is **v1.0.0**. Download the packaged ZIP and its SHA-256 checksum from GitHub Releases.

## Run

Extract the release package, keep the files together, then double-click:

`Start Keeper Group Export.vbs`

Normal launches use a previously verified Python runtime directly. On a clean machine the PowerShell bootstrap locates or installs Python 3.13 x64, enforces the pinned Keeper Commander dependency, verifies the runtime, and caches the verified launcher for subsequent fast starts.

## Features

- Keeper login, device approval and supported 2FA through Keeper Commander's `LoginUi`.
- Dynamic discovery of live Keeper folders; no organisational folders are hard-coded.
- Student / Email / Password preview and CSV export.
- Live preview search and preview-only password masking.
- Refresh Vault without forcing a new login.
- Remembers the last successful Keeper username locally on that PC only.
- Single-pass folder/record indexing after each vault sync.
- Fail-closed export if a Keeper record cannot be read.
- Professional About screen and programmer credits.

## Authentication support

The application supports Keeper's login/password flow plus the device-approval and 2FA channels implemented in the GUI, including authenticator codes, SMS, Duo, RSA SecurID, Keeper DNA and backup codes where Keeper exposes them.

**WebAuthn/security-key-only authentication is not currently driven by this Tkinter utility.** If an account exposes only that factor, the application reports the limitation and cancels the login rather than bypassing or weakening the account's security policy.

## Source layout

The stable entry point is `Keeper-Group-Export.pyw`. Focused modules live under `keeper_group_export/`:

- `app.py` — application composition and local non-secret settings.
- `auth_runtime.py` — deferred Keeper import/config handling.
- `auth_present.py` — login and authentication-choice presentation.
- `auth_flow.py` — Keeper device approval, 2FA and password flow.
- `ui_styles.py` / `ui_layout.py` / `ui_helpers.py` / `ui_actions.py` — desktop UI.
- `vault.py` — indexed folder discovery, preview and CSV export.
- `common.py` — application-local constants and pure helpers.

`requirements.txt` is the pinned runtime dependency source of truth. Windows CI compiles and imports the modules, runs unit tests, rejects wildcard local imports, and parses the PowerShell bootstrap.

## Privacy / security

**No Keeper username, email address, password, token, or vault data is hard-coded or shipped in this repository.**

A fresh installation starts with a blank username unless that PC already has a locally remembered username from a previous successful login. The remembered username is stored only under:

`%LOCALAPPDATA%\KeeperGroupExport\settings.json`

The application does not deliberately persist the Keeper master password. Exported CSV files contain plaintext passwords by design, so they must be treated as sensitive credential material.

If any Keeper record in the selected folder cannot be read, export is stopped rather than silently writing an incomplete credential list.

## Infiltratr Common

Keeper Group Export is **not currently linked to Infiltratr Common**. Common 1.14 is a native C11 library and currently has no supported Python binding for the facilities this application needs. Adding a private FFI layer solely to claim linkage would increase startup time, packaging complexity and failure surface without removing meaningful duplicated logic.

If Common gains a supported Python consumer interface for a genuinely shared contract used here, Keeper Group Export should pin and consume that interface.

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

Current stable version: **1.0.0**

Keeper and Keeper Commander are products of Keeper Security, Inc. This is an independent utility and not an official Keeper Security product.
