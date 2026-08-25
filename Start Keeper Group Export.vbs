' Keeper Group Export v3.8 - fast launcher
' ========================================
'
' Architectural role
' ------------------
' Keep normal startup as close to "double-click -> pythonw" as possible.
' PowerShell, winget and pip are first-run/repair concerns, not normal runtime
' dependencies.
'
' Fast-path precedence
' --------------------
' 1. Use the previously verified pythonw.exe path cached by the bootstrap.
' 2. Otherwise accept the known standard Python 3.13 per-user installation when
'    Keeper Commander is already present.
' 3. Only then invoke the PowerShell bootstrap.
'
' The launcher never handles Keeper usernames, passwords, session tokens or
' exported credential data.
'
Option Explicit

' Fast launcher. Normal launches bypass PowerShell prerequisite checks.
Dim fso, shell, base, appFile, runtimeRoot, markerFile
Dim pythonw, keeperDir, ts, cachedPythonw, ps1, cmd

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

' Resolve relative to this launcher, not the caller's current directory.
' That makes the extracted package relocatable as a complete folder.
base = fso.GetParentFolderName(WScript.ScriptFullName)
appFile = fso.BuildPath(base, "Keeper-Group-Export-v3.8.pyw")

runtimeRoot = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\KeeperGroupExport"
markerFile = fso.BuildPath(runtimeRoot, "runtime-v1.txt")

' runtime-v1.txt is created only after PowerShell has verified the runtime.
' Reading that cached absolute path is the cheapest and most reliable normal path.
If fso.FileExists(markerFile) Then
    Set ts = fso.OpenTextFile(markerFile, 1, False)
    If Not ts.AtEndOfStream Then
        cachedPythonw = Trim(ts.ReadLine)
    Else
        cachedPythonw = ""
    End If
    ts.Close

    If cachedPythonw <> "" Then
        If fso.FileExists(cachedPythonw) And fso.FileExists(appFile) Then
            shell.Run """" & cachedPythonw & """ """ & appFile & """", 0, False
            WScript.Quit 0
        End If
    End If
End If

' Compatibility fast path for machines prepared before the marker existed.
' These are intentionally cheap file/folder tests; a broken dependency will still
' surface explicitly when the GUI's background Keeper loader runs.
pythonw = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & _
          "\Programs\Python\Python313\pythonw.exe"
keeperDir = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & _
            "\Programs\Python\Python313\Lib\site-packages\keepercommander"

If fso.FileExists(pythonw) And fso.FolderExists(keeperDir) And fso.FileExists(appFile) Then
    shell.Run """" & pythonw & """ """ & appFile & """", 0, False
    WScript.Quit 0
End If

' No prepared runtime was found. Hand control to the slow bootstrap, which owns
' installation/repair, diagnostic logging and the eventual GUI launch.
ps1 = fso.BuildPath(base, "Keeper-Group-Export-Bootstrap.ps1")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """"
' 0 = hidden window. False = do not block WScript; PowerShell owns its own
' lifecycle and operator-facing error dialogs.
shell.Run cmd, 0, False
