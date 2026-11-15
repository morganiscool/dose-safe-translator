# Dose-Safe Translator: run the app on this Windows PC and give it a free public link.
#
# The app runs here; Cloudflare's free "quick tunnel" gives it an https://....trycloudflare.com
# address anyone can open. The link works only while this window is open and the PC is awake,
# and it changes every time you start it.
#
# First run: sets up Python packages (about 1 GB) and downloads cloudflared from Cloudflare's
# GitHub releases, into %LOCALAPPDATA%\dose-safe-translator (outside OneDrive). The translation
# model (about 2.5 GB) downloads the first time the app starts.

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
$appHome = Join-Path $env:LOCALAPPDATA "dose-safe-translator"
$python = Join-Path $appHome "venv\Scripts\python.exe"
$cloudflared = Join-Path $appHome "cloudflared.exe"
$port = 7860
New-Item -ItemType Directory -Force $appHome | Out-Null

$requirements = Join-Path $repo "requirements-app.txt"
$installed = Join-Path $appHome "installed-requirements.txt"  # what the last successful install used
$firstRun = -not (Test-Path $python)
if ($firstRun) {
    Write-Host "First run: installing the app's Python packages (about 1 GB, a few minutes)..."
    $base = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python" }
    & $base -m venv (Join-Path $appHome "venv")
}
# Install again whenever requirements-app.txt changes (photo mode added packages on Nov 15, 2026).
if ($firstRun -or -not (Test-Path $installed) -or
    (Get-FileHash $requirements).Hash -ne (Get-FileHash $installed).Hash) {
    if (-not $firstRun) { Write-Host "The app's package list changed: updating its Python packages..." }
    & $python -m pip install --disable-pip-version-check --extra-index-url https://download.pytorch.org/whl/cpu -r $requirements
    if ($LASTEXITCODE -ne 0) { throw "Installing the Python packages failed. Check the internet connection and run this again." }
    Copy-Item $requirements $installed
}
if (-not (Test-Path $cloudflared)) {
    Write-Host "First run: downloading cloudflared from Cloudflare's GitHub releases..."
    Invoke-WebRequest -UseBasicParsing -OutFile $cloudflared `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    if ((Get-AuthenticodeSignature $cloudflared).Status -ne "Valid") {
        Remove-Item $cloudflared
        throw "The downloaded cloudflared isn't signed by Cloudflare, so it was deleted. Try again later."
    }
}

if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
    throw "Something is already using port $port. Close the other copy of the app first."
}

Write-Host "Starting the app..."
$server = Start-Process -FilePath $python -PassThru -NoNewWindow `
    -ArgumentList "-m", "uvicorn", "server:app", "--app-dir", "`"$repo`"", "--port", "$port"
try {
    $up = $false
    for ($i = 0; $i -lt 60 -and -not $up; $i++) {
        Start-Sleep -Seconds 1
        try { Invoke-WebRequest -UseBasicParsing "http://localhost:$port/api/status" | Out-Null; $up = $true } catch {}
    }
    if (-not $up) { throw "The app didn't start. Look at the messages above for the reason." }
    Write-Host "The app is running at http://localhost:$port/translate"
    Write-Host "Opening the public link (keep this window open and the PC awake)..."

    # cloudflared writes its messages to stderr; Windows PowerShell would treat each line as an
    # error, so they go to a log file and the link is read from there.
    $log = Join-Path $appHome "cloudflared.log"
    Remove-Item $log -ErrorAction SilentlyContinue
    $tunnel = Start-Process -FilePath $cloudflared -PassThru -NoNewWindow -RedirectStandardError $log `
        -ArgumentList "tunnel", "--no-autoupdate", "--url", "http://localhost:$port"
    $link = $null
    for ($i = 0; $i -lt 60 -and -not $link; $i++) {
        Start-Sleep -Seconds 1
        if ($tunnel.HasExited) { throw "Cloudflare's tunnel stopped. Its messages are in $log" }
        $found = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($found) { $link = $found.Matches[0].Value }
    }
    if (-not $link) { throw "No public link after a minute. Cloudflare's messages are in $log" }

    Set-Content -Path (Join-Path $appHome "public-link.txt") -Value $link -Encoding utf8
    Write-Host ""
    Write-Host "  Your public link:  $link" -ForegroundColor Green
    Write-Host "  Translator:        $link/translate" -ForegroundColor Green
    Write-Host "  (Press Ctrl+C or close this window to stop.)"
    Write-Host ""
    Wait-Process -Id $tunnel.Id
}
finally {
    if ($tunnel -and -not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id -Force }
    if ($server -and -not $server.HasExited) { Stop-Process -Id $server.Id -Force }
}
