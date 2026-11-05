# Orbit on native Windows: what the kit needs, installed once, from official sources. Run it in PowerShell:
#
#   powershell -ExecutionPolicy Bypass -File setup-windows.ps1          asks about the voice-notes tools
#   powershell -ExecutionPolicy Bypass -File setup-windows.ps1 -Yes     asks nothing, skips the optional
#
# It installs: Python 3 (your user only; it also gives the service its pythonw.exe), git, ffmpeg (voice
# notes), tesseract with Arabic (reading scans and photos), the MXC sandbox runtime (the thing that keeps
# your crew in its own folder and on the sites you approve) and the Python packages the kit uses.
# Windows 11 22H2 or newer is required for the sandbox. Nothing system-wide changes; safe to run again.
param([switch]$Yes = $false)
$ErrorActionPreference = "Stop"
$KIT = Split-Path -Parent $MyInvocation.MyCommand.Path

Function Step($n, $msg) { Write-Host "`n$n  $msg" }

# ------------------------------------------------------------------------
# The MXC sandbox runtime, pinned now so a later release can't drift in unannounced.
# Filled at packaging time with the official artifact's release, URL and checksum;
# Get-FileHash must match exactly, or the runtime is not installed.
$MXC_VERSION = ""
$MXC_URL     = ""
$MXC_SHA256  = ""
# ------------------------------------------------------------------------

Function Have($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# 0/ the Windows itself: process containers need 22H2 or newer
$build = [version](Get-CimInstance Win32_OperatingSystem).Version
if ($build -lt [version]"10.0.22621") {
    Step "0/4" "Windows $build"
    Write-Host "   Orbit's sandbox needs Windows 11 22H2 or newer (this is $build)."
    Write-Host "   Without it the crew runs in WSL2 mode instead: install WSL and use the"
    Write-Host "   Linux steps in docs/SETUP.md ('Windows through WSL')."
    exit 1
}

Step "1/4" "The programs (winget installs them for you, no admin)…"
foreach ($id in @("Python.Python.3.12", "Git.Git", "Gyan.FFmpeg", "UB-Mannheim.TesseractOCR")) {
    if (Have "winget") {
        winget install --id $id -e --silent --accept-package-agreements --accept-source-agreements 2>$null
        if ($LASTEXITCODE -eq -1978335135) { Write-Host "   $id is already installed" } # "No package found" = up to date
    } else {
        Write-Host "   winget is missing. Install it (Microsoft Store: 'App Installer'), then run this again."
        exit 1
    }
}

Step "2/4" "The MXC sandbox runtime (the boundary for every shell command your crew runs)…"
$VENDOR = Join-Path $KIT "vendor\mxc"
New-Item -ItemType Directory -Force -Path $VENDOR | Out-Null
if (-not $MXC_URL) {
    Write-Host "   The packaged runtime isn't pinned in this copy (MXC_URL is empty)."
    Write-Host "   Put the executor (wxc-exec.exe) from the official MXC release into:"
    Write-Host "     $VENDOR"
    Write-Host "   and store its version in:  $VENDOR\version.txt"
} else {
    $EXE = Join-Path $VENDOR "wxc-exec.exe"
    Invoke-WebRequest -Uri $MXC_URL -OutFile $EXE -UseBasicParsing
    $hash = (Get-FileHash $EXE -Algorithm SHA256).Hash.ToLower()
    if ($hash -ne $MXC_SHA256.ToLower()) {
        Remove-Item $EXE
        Write-Host "   The downloaded runtime doesn't match the pinned checksum (got $hash)."
        Write-Host "   Nothing was kept. Check the release notes, then run this again."
        exit 1
    }
    Set-Content -Path (Join-Path $VENDOR "version.txt") -Value $MXC_VERSION
    Write-Host "   MXC runtime v$MXC_VERSION installed (checksum verified)."
}

Step "3/4" "Python packages for the page reader, the browser, the chat channels and documents (your user only)…"
python -m pip install --user --quiet --upgrade requests beautifulsoup4 playwright websocket-client pypdf
python -m playwright install chromium

Step "4/4" "Next steps (in this window)…"
Write-Host "   1. Claude Code, if the crew's brain isn't on this PC yet: git clone or download from"
Write-Host "      https://claude.com/claude-code, then run  claude auth login  with your own account."
Write-Host "   2. Set up the team:  python `"$KIT\orbit`" setup"
Write-Host "      (checks, your business, your chat bot, your first hire)."
Write-Host ""
Write-Host "Done. If anything failed, rerun this script; each step is safe to repeat."
Write-Host "Later:  orbit doctor  checks everything and tells you the fix in plain words."
