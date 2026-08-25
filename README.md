# Keeper Group Export

Keeper Group Export is a small Windows GUI utility for exporting credential records from a selected live Keeper folder to a clean CSV containing only:

- Student
- Email
- Password

It is intended for authorised administrative use where a Keeper folder needs to be turned into a simple, parent-ready credential list without exporting the entire vault.

## Features

- Authenticates to Keeper at application startup.
- Supports Keeper device approval and 2FA through Keeper Commander's LoginUi flow.
- Discovers Keeper folders dynamically from the live vault; no school-year or organisational folders are hard-coded.
- Previews Student / Email / Password records before export.
- Live preview search.
- Optional preview-only password masking.
- Refreshes the connected vault without forcing reauthentication.
- Exports UTF-8 CSV suitable for Microsoft Excel.
- Remembers only the last successfully used Keeper username on the local PC.
- Does **not** ship with or hard-code any Keeper username, email address, password, token, or vault data.

## Running

Extract the files and double-click:

`Start Keeper Group Export.vbs`

Normal launches use an already-prepared Python runtime directly. On a new PC, the PowerShell bootstrap can install/prepare Python 3.13 x64 and Keeper Commander 18.1.2 before launching the GUI.

The first preparation on a clean PC can take longer than subsequent launches.

## Security

The application does not persist the Keeper master password. The last successful Keeper username is stored only in the user's local application-data folder for convenience.

The exported CSV intentionally contains plaintext passwords. Treat exported files as sensitive credential material and store/share them accordingly.

Local runtime state is kept under:

`%LOCALAPPDATA%\KeeperGroupExport`

No local account settings or exported CSV files are included in this repository.

## Keyboard shortcuts

- `Ctrl+F` — focus preview search
- `F5` — refresh connected Keeper vault
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

## Project status

Current version: **3.8**

Keeper and Keeper Commander are products of Keeper Security, Inc. This project is an independent utility and is not an official Keeper Security product.
