<#
.SYNOPSIS
    First-run/repair bootstrap for Keeper Group Export v3.5.

.DESCRIPTION
    This is intentionally the slow path. Normal launches are handled directly
    by the VBScript launcher once a verified runtime is available.

    Dependency order:
      1. Locate Python 3.13 x64.
      2. Install it with winget when absent.
      3. Verify/repair pip.
      4. Verify/install keepercommander==18.1.2.
      5. Smoke-test Keeper Commander + Tkinter.
      6. Resolve pythonw.exe.
      7. Cache its path for future fast launches.
      8. Launch the GUI.

    Native stdout/stderr is captured explicitly. Windows PowerShell can
    otherwise promote native stderr into a terminating error under
    $ErrorActionPreference="Stop", hiding the child exit code and producing
    truncated "Traceback..." diagnostics.

.IMPLEMENTATION NOTES
    Python architecture is read from the executable's PE/COFF Machine field,
    rather than platform.machine(). On Windows ARM64, x64 Python running under
    emulation can still report ARM64 as the host architecture.

      IMAGE_FILE_MACHINE_AMD64 = 0x8664
      IMAGE_FILE_MACHINE_ARM64 = 0xAA64

.SECURITY
    This bootstrap never reads or stores Keeper credentials.

.DIAGNOSTICS
    %LOCALAPPDATA%\KeeperGroupExport\bootstrap.log

    Successful runtime cache:
    %LOCALAPPDATA%\KeeperGroupExport\runtime-v1.txt
#>

param()

# PowerShell-native failures terminate preparation. Native programs are wrapped
# by Invoke-Native so their exit codes remain explicit data.
$ErrorActionPreference = "Stop"

# Resolve all package members relative to this script rather than the caller's
# working directory, so the extracted folder is relocatable as a unit.
$AppName = "Keeper Group Export"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppFile = Join-Path $AppDir "Keeper-Group-Export-v3.8.pyw"
$RuntimeRoot = Join-Path $env:LOCALAPPDATA "KeeperGroupExport"
$LogFile = Join-Path $RuntimeRoot "bootstrap.log"
$MarkerFile = Join-Path $RuntimeRoot "runtime-v1.txt"

New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null

function Log([string]$Text) {
    <#
    .SYNOPSIS
        Append one timestamped diagnostic line.
    .PARAMETER Text
        Human-readable bootstrap state or error information.
    #>
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$stamp $Text" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

function Show-Error([string]$Text) {
    <#
    .SYNOPSIS
        Display an operator-visible error while PowerShell itself is hidden.
    #>
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $Text,
        $AppName,
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

function Invoke-Native {
    <#
    .SYNOPSIS
        Execute a native process and return ExitCode/StdOut/StdErr as data.
    .DESCRIPTION
        Temporary-file redirection prevents Python/pip stderr from being confused
        with PowerShell's own error stream.
    #>
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()

    try {
        $process = Start-Process `
            -FilePath $FilePath `
            -ArgumentList $Arguments `
            -Wait `
            -PassThru `
            -NoNewWindow `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr

        $outText = ""
        $errText = ""

        if (Test-Path $stdout) {
            $outText = Get-Content -LiteralPath $stdout -Raw -ErrorAction SilentlyContinue
        }
        if (Test-Path $stderr) {
            $errText = Get-Content -LiteralPath $stderr -Raw -ErrorAction SilentlyContinue
        }

        [PSCustomObject]@{
            ExitCode = $process.ExitCode
            StdOut   = ($outText | Out-String).Trim()
            StdErr   = ($errText | Out-String).Trim()
        }
    }
    finally {
        Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue
    }
}

function Log-NativeFailure([string]$Stage, $Result) {
    # Preserve complete native diagnostics in the file log while user-facing
    # dialogs remain concise.
    Log "$Stage failed with exit code $($Result.ExitCode)."
    if ($Result.StdOut) { Log "$Stage stdout: $($Result.StdOut)" }
    if ($Result.StdErr) { Log "$Stage stderr: $($Result.StdErr)" }
}

function Get-PeMachine([string]$Path) {
    <#
    .SYNOPSIS
        Read the PE/COFF Machine field from a Windows executable.
    .RETURNS
        UInt16 machine value, or $null for a missing/unreadable/non-PE file.
    .NOTES
        DOS header offset 0x3C contains e_lfanew.
        e_lfanew points to "PE\0\0".
        The COFF Machine field follows that signature.
    #>
    if (-not (Test-Path -LiteralPath $Path)) {
        return $null
    }

    $stream = $null
    $reader = $null

    try {
        $stream = [System.IO.File]::Open(
            $Path,
            [System.IO.FileMode]::Open,
            [System.IO.FileAccess]::Read,
            [System.IO.FileShare]::ReadWrite
        )
        $reader = New-Object System.IO.BinaryReader($stream)

        # Read architecture from file metadata without executing the candidate.
        $stream.Seek(0x3C, [System.IO.SeekOrigin]::Begin) | Out-Null
        $peOffset = $reader.ReadInt32()

        $stream.Seek($peOffset, [System.IO.SeekOrigin]::Begin) | Out-Null
        $signature = $reader.ReadUInt32()
        if ($signature -ne 0x00004550) {
            return $null
        }

        return $reader.ReadUInt16()
    }
    catch {
        return $null
    }
    finally {
        if ($reader) { $reader.Dispose() }
        elseif ($stream) { $stream.Dispose() }
    }
}

function Test-X64Python([string]$Path) {
    # 0x8664 = IMAGE_FILE_MACHINE_AMD64. Host architecture is deliberately
    # irrelevant because Windows ARM64 can run x64 Python under emulation.
    return ((Get-PeMachine $Path) -eq 0x8664)
}

function Add-PythonCandidate([System.Collections.Generic.List[string]]$List, [string]$Path) {
    # Discovery and validation are separate: registry/launcher sources can
    # contain duplicates, stale paths or ARM64 interpreters.
    if (-not $Path) { return }

    try {
        $resolved = [System.IO.Path]::GetFullPath($Path)
    }
    catch {
        return
    }

    if ((Test-Path -LiteralPath $resolved) -and (-not $List.Contains($resolved))) {
        $List.Add($resolved)
    }
}

function Find-Python313X64 {
    <#
    .SYNOPSIS
        Locate Python 3.13 whose executable is genuinely AMD64/x64.
    .DESCRIPTION
        Search standard per-user installation, PythonCore registry locations,
        then py.exe. Every candidate is independently PE-verified.
    #>
    $candidates = New-Object 'System.Collections.Generic.List[string]'

    Add-PythonCandidate $candidates (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe")

    # Cover per-user and machine registrations. WOW6432Node is included
    # defensively for enterprise images with unusual registration state.
    $registryKeys = @(
        "HKCU:\Software\Python\PythonCore\3.13\InstallPath",
        "HKLM:\Software\Python\PythonCore\3.13\InstallPath",
        "HKLM:\Software\WOW6432Node\Python\PythonCore\3.13\InstallPath"
    )

    foreach ($key in $registryKeys) {
        if (Test-Path $key) {
            try {
                $installDir = (Get-Item $key).GetValue("")
                if ($installDir) {
                    Add-PythonCandidate $candidates (Join-Path $installDir "python.exe")
                }
            }
            catch {
            }
        }
    }

    # py.exe is a discovery source, not an authority. Its result still has to
    # pass PE verification before it can become the selected runtime.
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $probe = Invoke-Native $launcher.Source @(
            "-3.13",
            "-c",
            "__import__('sys').stdout.write(__import__('sys').executable)"
        )
        if ($probe.ExitCode -eq 0 -and $probe.StdOut) {
            Add-PythonCandidate $candidates $probe.StdOut
        }
    }

    foreach ($candidate in $candidates) {
        $machine = Get-PeMachine $candidate
        if ($machine -eq 0x8664) {
            Log ("Found x64 Python candidate: {0}" -f $candidate)
            return $candidate
        }
        elseif ($machine -eq 0xAA64) {
            Log ("Ignoring ARM64 Python candidate: {0}" -f $candidate)
        }
    }

    return $null
}

try {
    Log "Starting prerequisite check."

    # Once selected, $Python is used explicitly for every pip/Keeper command.
    # Nothing later is allowed to fall back implicitly to PATH.

    $Python = Find-Python313X64

    if (-not $Python) {
        Log "Python 3.13 x64 not found. Attempting automatic install."

        # winget keeps package identity, source and requested architecture
        # explicit; avoid an opaque ad-hoc installer download.
        $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $Winget) {
            throw "Python 3.13 x64 is required and Windows Package Manager (winget) is not available."
        }

        $install = Invoke-Native $Winget.Source @(
            "install",
            "--id", "Python.Python.3.13",
            "-e",
            "--architecture", "x64",
            "--source", "winget",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--silent"
        )

        if ($install.ExitCode -ne 0 -and $install.ExitCode -ne -1978335189) {
            Log-NativeFailure "Python installation" $install
            throw "Python installation failed. See bootstrap.log for details."
        }

        # Registration/path visibility can lag slightly behind winget completion.
        # Retry for a bounded period before declaring discovery failure.
        for ($i = 0; $i -lt 20 -and -not $Python; $i++) {
            Start-Sleep -Seconds 1
            $Python = Find-Python313X64
        }

        if (-not $Python) {
            throw "Python 3.13 x64 was installed, but the bootstrap could not locate an x64 python.exe."
        }

        Log "Python 3.13 x64 installed at $Python."
    }
    else {
        Log "Python 3.13 x64 ready at $Python."
    }

    # Always invoke pip through the selected interpreter; pip.exe on PATH may
    # belong to a different Python installation.
    $pip = Invoke-Native $Python @("-m", "pip", "--version")
    if ($pip.ExitCode -ne 0) {
        Log-NativeFailure "pip probe" $pip
        Log "pip unavailable or unhealthy. Running ensurepip."

        # ensurepip is the standard-library recovery path and avoids introducing
        # another downloader just to repair pip.
        $ensurePip = Invoke-Native $Python @("-m", "ensurepip", "--upgrade")
        if ($ensurePip.ExitCode -ne 0) {
            Log-NativeFailure "ensurepip" $ensurePip
            throw "Python installed, but pip could not be prepared. See bootstrap.log."
        }

        $pip = Invoke-Native $Python @("-m", "pip", "--version")
        if ($pip.ExitCode -ne 0) {
            Log-NativeFailure "pip recheck" $pip
            throw "pip is still unavailable after ensurepip. See bootstrap.log."
        }
    }

    # Test the selected interpreter's ability to execute Keeper Commander,
    # rather than trusting package metadata from some other environment.
    $keeper = Invoke-Native $Python @("-m", "keepercommander", "--version")
    if ($keeper.ExitCode -ne 0) {
        Log-NativeFailure "Keeper Commander probe" $keeper
        Log "Keeper Commander missing. Installing version 18.1.2."

        # Pin the version used during development/testing. An unconstrained
        # startup-time upgrade would change behaviour outside this app's release.
        $installKeeper = Invoke-Native $Python @(
            "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-input",
            "keepercommander==18.1.2"
        )

        if ($installKeeper.ExitCode -ne 0) {
            Log-NativeFailure "Keeper Commander installation" $installKeeper
            throw "Keeper Commander installation failed. See bootstrap.log."
        }

        Log "Keeper Commander installed."
    }

    # Smoke-test while stdout/stderr are still visible to the bootstrap. Once
    # pythonw.exe starts, import failures would otherwise be much less obvious.
    $verify = Invoke-Native $Python @(
        "-c",
        "__import__('keepercommander');__import__('tkinter')"
    )
    if ($verify.ExitCode -ne 0) {
        Log-NativeFailure "Runtime verification" $verify
        throw "Keeper runtime verification failed. See bootstrap.log."
    }

    if (-not (Test-Path $AppFile)) {
        throw "Application file not found: $AppFile"
    }

    # pythonw avoids a console on normal GUI launches. Fall back only to the
    # already-verified python.exe, never to an unrelated pythonw on PATH.
    $PythonW = Join-Path (Split-Path -Parent $Python) "pythonw.exe"
    if (-not (Test-X64Python $PythonW)) {
        $PythonW = $Python
    }

    # Cache only the verified launcher path. The VBS fast path can consume this
    # in milliseconds without paying PowerShell/pip discovery cost again.
    $PythonW | Out-File -FilePath $MarkerFile -Encoding ascii -Force
    Log "Runtime ready. Cached launcher: $PythonW"

    Start-Process -FilePath $PythonW` -ArgumentList "`"$AppFile`"" -WorkingDirectory $AppDir
    exit 0
}
catch {
    # Detailed child-process evidence is already in bootstrap.log; the dialog
    # remains concise and points the tester to that file.
    Log "ERROR: $($_.Exception.Message)"
    Show-Error(
        "Keeper Group Export could not prepare its runtime.`r`n`r`n" +
        $_.Exception.Message +
        "`r`n\r`nLog: $LogFile"
    )
    exit 1
}
