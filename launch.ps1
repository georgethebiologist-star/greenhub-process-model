#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Set up and launch the local GreenHub application on Windows.
.DESCRIPTION
    Creates the project virtual environment when needed, installs Python and
    frontend dependencies, starts the API and UI, waits for readiness, and
    stops both child processes when this window is closed with Ctrl+C.
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendRoot = Join-Path $projectRoot 'frontend'
$pythonEnv = Join-Path $projectRoot '.venv'
$pythonExe = Join-Path $pythonEnv 'Scripts\python.exe'
$dependencyState = Join-Path $pythonEnv 'greenhub-install-state.json'
$logRoot = Join-Path $env:TEMP 'GreenHub\logs'
$apiLog = Join-Path $logRoot 'api.log'
$apiErrorLog = Join-Path $logRoot 'api-error.log'
$uiLog = Join-Path $logRoot 'ui.log'
$uiErrorLog = Join-Path $logRoot 'ui-error.log'
$apiProcess = $null
$uiProcess = $null
$freshPythonEnv = $false

function Stop-ChildProcess($process) {
    if ($null -ne $process -and -not $process.HasExited) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        $process.WaitForExit()
    }
}

try {
    if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Get-Command corepack -ErrorAction SilentlyContinue)) {
        throw 'Node.js 24.x with Corepack is required for the local web interface. Install Node.js 24 LTS from https://nodejs.org/.'
    }

    $nodeVersion = (& node --version).Trim().TrimStart('v').Split('.')
    if ([int]$nodeVersion[0] -ne 24) {
        throw "Node.js 24.x with Corepack is required; found $(& node --version)."
    }

    if (-not (Test-Path $pythonExe)) {
        $pythonCommand = $null
        $pythonPrefixArgs = @()
        $pythonVersionOutput = $null
        $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
        if ($pythonLauncher) {
            try {
                $pythonVersionOutput = & $pythonLauncher.Source -3.12 -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>$null
                if ($LASTEXITCODE -eq 0) {
                    $pythonCommand = $pythonLauncher.Source
                    $pythonPrefixArgs = @('-3.12')
                } else {
                    $pythonVersionOutput = $null
                }
            } catch {
                $pythonVersionOutput = $null
            }
        }
        if (-not $pythonVersionOutput) {
            $pythonExecutable = Get-Command python -ErrorAction SilentlyContinue
            if ($pythonExecutable) {
                try {
                    $pythonVersionOutput = & $pythonExecutable.Source -c 'import sys; print(sys.version_info.major, sys.version_info.minor)' 2>$null
                    if ($LASTEXITCODE -eq 0) { $pythonCommand = $pythonExecutable.Source }
                    else { $pythonVersionOutput = $null }
                } catch {
                    $pythonVersionOutput = $null
                }
            }
        }
        if (-not $pythonVersionOutput) {
            throw 'CPython 3.12.x is required. Install the official Python Install Manager, then run py install 3.12 in PowerShell: https://docs.python.org/3/using/windows.html'
        }
        $pythonVersion = ($pythonVersionOutput -join ' ').Trim() -replace '\s+', '.'
        $parts = $pythonVersion.Split('.') | ForEach-Object { [int]$_ }
        if ($parts[0] -ne 3 -or $parts[1] -ne 12) {
            throw "CPython 3.12.x is required; found $pythonVersion. Install it with py install 3.12, then launch again."
        }
        Write-Host 'Creating the Python environment (first launch only)...'
        & $pythonCommand @pythonPrefixArgs -m venv $pythonEnv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
        $freshPythonEnv = $true
    }
    $venvVersionOutput = & $pythonExe -c 'import sys; print(sys.version_info.major, sys.version_info.minor)'
    if ($LASTEXITCODE -ne 0) { throw 'Could not read the project Python environment version.' }
    $venvVersion = ($venvVersionOutput -join ' ').Trim() -replace '\s+', '.'
    $venvParts = $venvVersion.Split('.') | ForEach-Object { [int]$_ }
    if ($venvParts[0] -ne 3 -or $venvParts[1] -ne 12) {
        throw "The project environment uses Python $venvVersion; CPython 3.12.x is required. Remove this project's .venv folder and launch again."
    }

    if (-not $SkipInstall) {
        $requirementsHash = (Get-FileHash (Join-Path $projectRoot 'requirements.txt') -Algorithm SHA256).Hash
        $packageHash = (Get-FileHash (Join-Path $frontendRoot 'package.json') -Algorithm SHA256).Hash
        $lockHash = (Get-FileHash (Join-Path $frontendRoot 'pnpm-lock.yaml') -Algorithm SHA256).Hash
        $tsxCli = Join-Path $frontendRoot 'node_modules\tsx\dist\cli.mjs'
        $installDependencies = $freshPythonEnv -or -not (Test-Path $dependencyState) -or -not (Test-Path $tsxCli)
        if (Test-Path $dependencyState) {
            try {
                $installed = Get-Content $dependencyState -Raw | ConvertFrom-Json
                if ($installed.requirements -ne $requirementsHash -or $installed.frontend_package -ne $packageHash -or $installed.frontend_lock -ne $lockHash) { $installDependencies = $true }
            } catch { $installDependencies = $true }
        }
        if ($installDependencies) {
            Write-Host 'Installing Python packages...'
            & $pythonExe -m pip install -r (Join-Path $projectRoot 'requirements.txt')
            if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
            Write-Host 'Installing locked web interface packages...'
            Push-Location $frontendRoot
            try {
                & corepack pnpm install --frozen-lockfile
                if ($LASTEXITCODE -ne 0) { throw 'Web interface dependency installation failed.' }
            } finally { Pop-Location }
            @{ requirements = $requirementsHash; frontend_package = $packageHash; frontend_lock = $lockHash } |
                ConvertTo-Json | Set-Content -LiteralPath $dependencyState -Encoding utf8
        }
    }

    New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
    $tsxCli = Join-Path $frontendRoot 'node_modules\tsx\dist\cli.mjs'
    if (-not (Test-Path $tsxCli)) { throw 'The web interface command was not installed. Rerun the launcher to install packages.' }
    $env:GREENHUB_API_HOST = '127.0.0.1'
    $env:GREENHUB_API_PORT = '8000'
    $env:GREENHUB_BACKEND_URL = 'http://127.0.0.1:8000'
    $env:GREENHUB_WEB_HOST = '127.0.0.1'
    $env:PORT = '3000'
    $env:NODE_ENV = 'development'
    $apiProcess = Start-Process -FilePath $pythonExe -ArgumentList @('-m','api') -WorkingDirectory $projectRoot -PassThru -RedirectStandardOutput $apiLog -RedirectStandardError $apiErrorLog -WindowStyle Hidden
    $uiProcess = Start-Process -FilePath 'node' -ArgumentList @($tsxCli, 'server.ts') -WorkingDirectory $frontendRoot -PassThru -RedirectStandardOutput $uiLog -RedirectStandardError $uiErrorLog -WindowStyle Hidden

    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        if ($apiProcess.HasExited) { throw "Python API stopped unexpectedly. Review $apiLog." }
        if ($uiProcess.HasExited) { throw "Web interface stopped unexpectedly. Review $uiLog." }
        try {
            $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 2
            $page = Invoke-WebRequest -Uri 'http://127.0.0.1:3000/' -TimeoutSec 2 -UseBasicParsing
            if ($health.status -eq 'ok' -and $page.StatusCode -eq 200) { $ready = $true; break }
        } catch { Start-Sleep -Seconds 1 }
    }
    if (-not $ready) { throw "GreenHub did not become ready in 60 seconds. Review $apiLog and $uiLog." }

    Write-Host ''
    Write-Host 'GreenHub is ready at http://127.0.0.1:3000/' -ForegroundColor Green
    Write-Host 'Keep this window open while using GreenHub. Press Ctrl+C here to stop it.'
    Start-Process 'http://127.0.0.1:3000/'
    while (-not $apiProcess.HasExited -and -not $uiProcess.HasExited) { Start-Sleep -Seconds 1 }
    if ($apiProcess.HasExited -or $uiProcess.HasExited) { throw "A GreenHub service stopped. Review $apiLog and $uiLog." }
} catch {
    Write-Host "`nGreenHub could not start: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Logs (when created): $logRoot"
    exit 1
} finally {
    Stop-ChildProcess $uiProcess
    Stop-ChildProcess $apiProcess
}
