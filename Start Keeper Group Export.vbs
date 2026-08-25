' Keeper Group Export 1.0.0 - fast launcher
' ========================================
'
' Normal startup is intentionally just cached pythonw.exe -> GUI. PowerShell,
' winget and pip are first-run/repair concerns and are not paid on every launch.
'
Option Explicit

Dim fso, shell, base, appFile, runtimeRoot, markerFile
Dim ts, cachedPythonw, ps1, cmd

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

base = fso.GetParentFolderName(WScript.ScriptFullName)
appFile = fso.BuildPath(base, "Keeper-Group-Export.pyw")

runtimeRoot = shell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\KeeperGroupExport"
markerFile = fso.BuildPath(runtimeRoot, "runtime-v2.txt")

' runtime-v2.txt is written only after the current bootstrap verifies Python,
' pip, the exact pinned Keeper Commander version, Tkinter and the application.
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

' No current verified runtime marker exists. Hand control to the slow bootstrap.
ps1 = fso.BuildPath(base, "Keeper-Group-Export-Bootstrap.ps1")
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """"
shell.Run cmd, 0, False

