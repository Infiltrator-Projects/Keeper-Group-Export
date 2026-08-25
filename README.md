# Keeper Group Export

Keeper Group Export is a Windows GUI utility for exporting credential records from a selected live Keeper folder to a clean CSV containing only **Student**, **Email**, and **Password**.

## Download / run

Use the tested source package in this repository:

`Keeper-Group-Export-v3.8.zip`

Extract it, then double-click:

`Start Keeper Group Export.vbs`

The first run on a clean PC may prepare Python 3.13 x64 and Keeper Commander 18.1.2. Later launches use the prepared runtime directly.

## Features

- Keeper login, device approval and 2FA through Keeper Commander's LoginUi flow.
- Dynamic discovery of live Keeper folders; no school-year folders are hard-coded.
- Student / Email / Password preview.
- Live preview search.
- Preview-only password masking.
- Refresh Vault without forcing a new login.
- UTF-8 CSV export for Microsoft Excel.
- Last successful Keeper username remembered locally on that PC only.
- Professional About screen and programmer credits.

## Privacy / security

**No Keeper username, email address, password, token, or vault data is hard-coded or shipped in this repository.**

A fresh installation therefore starts with a blank username unless that PC already has a local setting saved by a previous successful login.

The remembered username is stored locally under:

`%LOCALAPPDATA%\KeeperGroupExport\settings.json`

That local file is not part of the source package or repository.

The application never deliberately persists the Keeper master password. Exported CSV files do contain plaintext passwords by design, so they must be treated as sensitive credential material.

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
