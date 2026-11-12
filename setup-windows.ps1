# Orbit on native Windows: what the kit needs, installed once, from official sources. Run it in PowerShell:
#
#   powershell -ExecutionPolicy Bypass -File setup-windows.ps1          asks about the voice-notes tools
#   powershell -ExecutionPolicy Bypass -File setup-windows.ps1 -Yes     asks nothing, skips the optional
#
# It installs: Python 3 (your user only; it also gives the service its pythonw.exe), git, ffmpeg (voice
# notes), tesseract with Arabic (reading scans and photos), the MXC sandbox runtime (the thing that keeps
# your crew in its own folder and on the sites you approve) and the Python packages the kit uses.
# Windows 11 24H2 with the current ProcessContainer updates (or newer) is required for the sandbox.
# Nothing system-wide changes; safe to run again.
param([switch]$Yes = $false)
$ErrorActionPreference = "Stop"
$KIT = Split-Path -Parent $MyInvocation.MyCommand.Path

Function Step($n, $msg) { Write-Host "`n$n  $msg" }

# ------------------------------------------------------------------------
# The MXC sandbox runtime, pinned so a later release cannot drift in unannounced. Microsoft's
# official Node SDK package includes the signed native executors; Orbit extracts only wxc-exec.exe
# and does not install Node. Get-FileHash and Authenticode must both pass before the binary is kept.
$MXC_VERSION = "1.0.1"
$MXC_SCHEMA_VERSION = "1.0.0"
$MXC_URL     = "https://registry.npmjs.org/@microsoft/mxc-sdk/-/mxc-sdk-1.0.1.tgz"
$MXC_SHA256  = "416D9607C9D4652395D95C3D9C5F5605F1F2F845DA1A63228BEE41B7392CEF49"
# ------------------------------------------------------------------------

Function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# 0/ the Windows itself: MXC's ProcessContainer support starts on updated 24H2 builds
$build = [version](Get-CimInstance Win32_OperatingSystem).Version
if ($build -lt [version]"10.0.26100") {
    Step "0/5" "Windows $build"
    Write-Host "   Orbit's sandbox needs Windows 11 24H2 with current updates or newer (this is $build)."
    Write-Host "   Without it the crew runs in WSL2 mode instead: install WSL and use the"
    Write-Host "   Linux steps in docs/SETUP.md ('Windows through WSL')."
    exit 1
}

Step "1/5" "The programs (winget installs them for you, no admin)…"
foreach ($id in @("Python.Python.3.12", "Git.Git", "Gyan.FFmpeg", "UB-Mannheim.TesseractOCR")) {
    if (Have "winget") {
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements 2>$null
        if ($LASTEXITCODE -eq -1978335135) { Write-Host "   $id is already installed" } # "No package found" = up to date
    } else {
        Write-Host "   winget is missing. Install it (Microsoft Store: 'App Installer'), then run this again."
        exit 1
    }
}
$PYTHON = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $PYTHON) {
    $PYTHON = Get-ChildItem (Join-Path $env:LOCALAPPDATA "Programs\Python\Python*\python.exe") -ErrorAction SilentlyContinue |
              Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
}
if (-not $PYTHON) {
    Write-Host "   Python was installed but isn't visible yet. Open a new PowerShell window and run this script again."
    exit 1
}

Step "2/5" "The MXC sandbox runtime (the boundary for every shell command your crew runs)…"
$VENDOR = Join-Path $KIT "vendor\mxc"
New-Item -ItemType Directory -Force -Path $VENDOR | Out-Null
$EXE = Join-Path $VENDOR "wxc-exec.exe"
$VERSION_FILE = Join-Path $VENDOR "version.txt"
$SCHEMA_FILE = Join-Path $VENDOR "schema-version.txt"
$installed = if (Test-Path $VERSION_FILE) { (Get-Content $VERSION_FILE -Raw).Trim() } else { "" }
$signed = if (Test-Path $EXE) { (Get-AuthenticodeSignature $EXE).Status -eq "Valid" } else { $false }
if ($installed -eq $MXC_VERSION -and $signed) {
    Write-Host "   MXC runtime v$MXC_VERSION is already installed and signed."
} else {
    $ARCHIVE = Join-Path $env:TEMP "orbit-mxc-$MXC_VERSION-$PID.tgz"
    $STAGE = Join-Path $env:TEMP "orbit-mxc-$MXC_VERSION-$PID"
    Invoke-WebRequest -Uri $MXC_URL -OutFile $ARCHIVE -UseBasicParsing
    $hash = (Get-FileHash $ARCHIVE -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($hash -ne $MXC_SHA256.ToUpperInvariant()) {
        Remove-Item $ARCHIVE -Force
        Write-Host "   The downloaded runtime doesn't match the pinned checksum (got $hash)."
        Write-Host "   Nothing was kept. Check the release notes, then run this again."
        exit 1
    }
    $arch = if ([Runtime.InteropServices.RuntimeInformation]::OSArchitecture -eq "Arm64") { "arm64" } else { "x64" }
    New-Item -ItemType Directory -Force -Path $STAGE | Out-Null
    try {
        tar -xzf $ARCHIVE -C $STAGE "package/bin/$arch/wxc-exec.exe"
        if ($LASTEXITCODE -ne 0) { throw "Windows tar could not extract the MXC runtime" }
        $downloaded = Join-Path $STAGE "package\bin\$arch\wxc-exec.exe"
        if ((Get-AuthenticodeSignature $downloaded).Status -ne "Valid") {
            throw "the extracted MXC executor does not have a valid Microsoft signature"
        }
        Copy-Item $downloaded $EXE -Force
        [IO.File]::WriteAllText($VERSION_FILE, "$MXC_VERSION`n", (New-Object Text.UTF8Encoding $false))
        [IO.File]::WriteAllText($SCHEMA_FILE, "$MXC_SCHEMA_VERSION`n", (New-Object Text.UTF8Encoding $false))
    } finally {
        Remove-Item $ARCHIVE -Force -ErrorAction SilentlyContinue
        Remove-Item $STAGE -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "   MXC runtime v$MXC_VERSION installed (checksum and Microsoft signature verified)."
}

Step "3/5" "The orbit command (so 'orbit doctor' works in every new PowerShell window)…"
$SHIMS = Join-Path $env:LOCALAPPDATA "Programs\Orbit\bin"
New-Item -ItemType Directory -Force -Path $SHIMS | Out-Null
foreach ($name in @("orbit", "staff")) {
    # like install.sh's ~/.local/bin symlink on a Mac or Linux: the kit's script, by absolute path
    [IO.File]::WriteAllText((Join-Path $SHIMS "$name.cmd"),
        "@echo off`r`n`"$PYTHON`" `"$KIT\$name`" %*`r`n", (New-Object Text.ASCIIEncoding))
}
$upath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($upath -split ";") -notcontains $SHIMS) {
    [Environment]::SetEnvironmentVariable("Path", ($upath.TrimEnd(";") + ";" + $SHIMS), "User")
    Write-Host "   Added $SHIMS to your PATH: open a new window and `orbit` works everywhere."
} else {
    Write-Host "   The orbit command is in place."
}

Step "4/5" "Python packages for the page reader, the browser, the chat channels and documents (your user only)…"
# This is the native equivalent of install.sh's Python step: pypdf powers the document pipeline, and
# Playwright's package plus Chromium powers the same headless-browser flow on every platform.
& $PYTHON -m pip install --user --quiet --upgrade requests beautifulsoup4 playwright websocket-client pypdf
& $PYTHON -m playwright install chromium

Step "5/5" "Next steps (in this window)…"
Write-Host "   1. Claude Code, if the crew's brain isn't on this PC yet: install it from"
Write-Host "      https://claude.com/claude-code, then run this script again. Sign-in is Claude's own"
Write-Host "      business (use the connection you already have)."
Write-Host "   2. Set up the team (in a new PowerShell window, so the orbit command is on PATH):"
Write-Host "      orbit setup"
Write-Host "      (checks, your business, your chat bot, your first hire)."
Write-Host ""
Write-Host "Done. If anything failed, rerun this script; each step is safe to repeat."
Write-Host "Later:  orbit doctor  checks everything and tells you the fix in plain words."
