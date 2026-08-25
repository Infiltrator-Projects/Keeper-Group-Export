<#
.SYNOPSIS
    First-run/repair bootstrap for Keeper Group Export 1.0.0.

.DESCRIPTION
    This is intentionally the slow path. Normal launches use the runtime-v2
    marker and start pythonw.exe directly through the VBScript launcher.

    Dependency order:
      1. Locate Python 3.13 x64.
      2. Install it with winget when absent.
      3. Verify/repair pip.
      4. Enforce the exact Keeper Commander version in requirements.txt.
      5. Smoke-test Keeper Commander and Tkinter.
      6. Resolve pythonw.exe.
      7. Cache its path in runtime-v2.txt.
      8. Launch the GUI.

    Native stdout/stderr is captured explicitly. Windows PowerShell can otherwise
    promote native stderr into a terminating error under
    $ErrorActionPreference="Stop", obscuring the child exit code.

.IMPLEMENTATION NOTES
    Python architecture is read from the executable's PE/COFF Machine field,
    rather than platform.machine(). On Windows ARM64, x64 Python running under
    emulation can still report ARM64 as the host architecture.

      IMAGE_FILE_MACHINE_AMD64 = 0x8664
      IMAGE_FILE_MACHINE_ARM64 = 0xAA64

.SECURITY
    The bootstrap never reads or stores Keeper credentials.

.DIAGNOSTICS
    %LOCALAPPDATA%\KeeperGroupExport\bootstrap.log
#>

param()

$ErrorActionPreference = "Stop"

$AppName = "Keeper Group Export"
$AppDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppFile = Join-Path $AppDir "Keeper-Group-Export.pyw"
$RequirementsFile = Join-Path $AppDir "requirements.txt"
$RuntimeRoot = Join-Path $env:LOCALAPPDATA "KeeperGroupExport"
$LogFile = Join-Path $RuntimeRoot "bootstrap.log"
$MarkerFile = Join-Path $RuntimeRoot "runtime-v2.txt"

New-Item -ItemType Directory -Path $RuntimeRoot -Force | Out-Null

function Log([string]$Text) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$stamp $Text" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

function Show-Error([string]$Text) {
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        $Text,
        $AppName,
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

function Invoke-Native {
    <# Execute a native process and return ExitCode/StdOut/StdErr as data. #>
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
    Log "$Stage failed with exit code $($Result.ExitCode)."
    if ($Result.StdOut) { Log "$Stage stdout: $($Result.StdOut)" }
    if ($Result.StdErr) { Log "$Stage stderr: $($Result.StdErr)" }
}

function Get-PeMachine([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }

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
        $stream.Seek(0x3C, [System.IO.SeekOrigin]::Begin) | Out-Null
        $peOffset = $reader.ReadInt32()
        $stream.Seek($peOffset, [System.IO.SeekOrigin]::Begin) | Out-Null
        $signature = $reader.ReadUInt32()
        if ($signature -ne 0x00004550) { return $null }
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
    return ((Get-PeMachine $Path) -eq 0x8664)
}

function Add-PythonCandidate(
    [System.Collections.Generic.List[string]]$List,
    [string]$Path
) {
    if (-not $Path) { return }
    try { $resolved = [System.IO.Path]::GetFullPath($Path) }
    catch { return }

    if ((Test-Path -LiteralPath $resolved) -and (-not $List.Contains($resolved))) {
        $List.Add($resolved)
    }
}

function Find-Python313X64 {
    $candidates = New-Object 'System.Collections.Generic.List[string]'

    Add-PythonCandidate $candidates (
        Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe"
    )

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
                # Registry discovery is best-effort; continue to other sources.
            }
        }
    }

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

    if (-not (Test-Path -LiteralPath $RequirementsFile)) {
        throw "Pinned dependency file not found: $RequirementsFile"
    }

    $keeperRequirement = Get-Content -LiteralPath $RequirementsFile |
        Where-Object { $_ -match '^\s*keepercommander==' } |
        Select-Object -First 1

    if (-not $keeperRequirement) {
        throw "requirements.txt does not contain a pinned keepercommander version."
    }

    $ExpectedKeeperVersion = ($keeperRequirement -split '==', 2)[1].Trim()
    if (-not $ExpectedKeeperVersion) {
        throw "Could not parse the pinned Keeper Commander version."
    }

    $Python = Find-Python313X64

    if (-not $Python) {
        Log "Python 3.13 x64 not found. Attempting automatic install."
        $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if (-not $Winget) {
            throw "Python 3.13 x64 is required and winget is not available."
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

        for ($i = 0; $i -lt 20 -and -not $Python; $i++) {
            Start-Sleep -Seconds 1
            $Python = Find-Python313X64
        }

        if (-not $Python) {
            throw "Python 3.13 x64 was installed, but x64 python.exe was not found."
        }

        Log "Python 3.13 x64 installed at $Python."
    }
    else {
        Log "Python 3.13 x64 ready at $Python."
    }

    $pip = Invoke-Native $Python @("-m", "pip", "--version")
    if ($pip.ExitCode -ne 0) {
        Log-NativeFailure "pip probe" $pip
        Log "pip unavailable or unhealthy. Running ensurepip."
        $ensurePip = Invoke-Native $Python @("-m", "ensurepip", "--upgrade")
        if ($ensurePip.ExitCode -ne 0) {
            Log-NativeFailure "ensurepip" $ensurePip
            throw "Python installed, but pip could not be prepared. See bootstrap.log."
        }
    }

    $keeperVersion = Invoke-Native $Python @(
        "-c",
        "import importlib.metadata; print(importlib.metadata.version('keepercommander'), end='')"
    )

    if (
        $keeperVersion.ExitCode -ne 0 -or
        $keeperVersion.StdOut.Trim() -ne $ExpectedKeeperVersion
    ) {
        if ($keeperVersion.ExitCode -eq 0) {
            Log "Keeper Commander $($keeperVersion.StdOut.Trim()) found; enforcing $ExpectedKeeperVersion."
        }
        else {
            Log-NativeFailure "Keeper Commander version probe" $keeperVersion
            Log "Keeper Commander missing; installing pinned runtime dependency."
        }

        $installKeeper = Invoke-Native $Python @(
            "-m", "pip", "install",
            "--disable-pip-version-check",
            "--no-input",
            "-r", $RequirementsFile
        )
        if ($installKeeper.ExitCode -ne 0) {
            Log-NativeFailure "Keeper Commander installation" $installKeeper
            throw "Keeper Commander installation failed. See bootstrap.log."
        }
    }

    $verify = Invoke-Native $Python @(
        "-c",
        "__import__('keepercommander');__import__('tkinter')"
    )
    if ($verify.ExitCode -ne 0) {
        Log-NativeFailure "Runtime verification" $verify
        throw "Keeper runtime verification failed. See bootstrap.log."
    }

    if (-not (Test-Path -LiteralPath $AppFile)) {
        throw "Application file not found: $AppFile"
    }

    $PythonW = Join-Path (Split-Path -Parent $Python) "pythonw.exe"
    if (-not (Test-X64Python $PythonW)) { $PythonW = $Python }

    $PythonW | Out-File -FilePath $MarkerFile -Encoding ascii -Force
    Log "Runtime ready. Cached launcher: $PythonW"

    $launchArgs = '"{0}"' -f $AppFile
    Start-Process `
        -FilePath $PythonW `
        -ArgumentList $launchArgs `
        -WorkingDirectory $AppDir

    exit 0
}
catch {
    Log "ERROR: $($_.Exception.Message)"
    Show-Error(
        "Keeper Group Export could not prepare its runtime.`r`n`r`n" +
        "$($_.Exception.Message)`r`n`r`n" +
        "Log: $LogFile"
    )
    exit 1
}

