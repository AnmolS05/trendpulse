$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $RepoRoot "backend"
$FrontendDir = Join-Path $RepoRoot "frontend"
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$ViteScript = Join-Path $FrontendDir "node_modules\vite\bin\vite.js"
$DbPath = (Join-Path $RepoRoot "trendpulse.db") -replace "\\", "/"

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    if (-not (Test-Path $Path)) {
        return
    }

    foreach ($Entry in Get-Content $Path) {
        $Line = $Entry.Trim()
        if ($Line -and -not $Line.StartsWith("#") -and $Line.Contains("=")) {
            $Name, $Value = $Line -split "=", 2
            $Name = $Name.Trim()
            $Value = $Value.Trim().Trim('"').Trim("'")
            if ($Name) {
                [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
            }
        }
    }
}

function Invoke-Logged {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Message,
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    Write-Host ""
    Write-Host $Message -ForegroundColor Cyan
    & $Command
}

function Test-BackendDependencies {
    if (-not (Test-Path $PythonExe)) {
        return $false
    }

    & $PythonExe -c "import sqlalchemy, fastapi, uvicorn" *> $null
    return $LASTEXITCODE -eq 0
}

function Get-FreePort {
    param(
        [Parameter(Mandatory = $true)]
        [int] $PreferredPort
    )

    for ($Port = $PreferredPort; $Port -lt ($PreferredPort + 100); $Port++) {
        $Listener = $null
        try {
            $Listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
            $Listener.Start()
            return $Port
        }
        catch {
        }
        finally {
            if ($Listener) {
                $Listener.Stop()
            }
        }
    }

    throw "Could not find an available local port starting at $PreferredPort."
}

Set-Location $RepoRoot
Import-DotEnv (Join-Path $RepoRoot ".env")

if (-not (Test-Path $VenvDir)) {
    Invoke-Logged "Creating backend virtual environment..." {
        py -3 -m venv $VenvDir
    }
}

if (-not (Test-Path $PythonExe)) {
    throw "Could not find Python in the backend virtual environment: $PythonExe"
}

$RequirementsPath = Join-Path $BackendDir "requirements.txt"
if (-not (Test-BackendDependencies)) {
    Invoke-Logged "Installing backend dependencies..." {
        $CleanRequirements = Join-Path $env:TEMP "trendpulse-requirements.txt"
        ((Get-Content -Raw $RequirementsPath) -replace "`0", "") |
            Set-Content -NoNewline -Encoding utf8 $CleanRequirements
        & $PythonExe -m pip install --upgrade pip
        & $PythonExe -m pip install -r $CleanRequirements
        if (-not (Test-BackendDependencies)) {
            throw "Backend dependency installation did not complete successfully."
        }
    }
}

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Invoke-Logged "Installing frontend dependencies..." {
        Set-Location $FrontendDir
        npm install
        Set-Location $RepoRoot
    }
}

$BackendPort = Get-FreePort 8000
$FrontendPort = Get-FreePort 5173
$ApiUrl = "http://localhost:$BackendPort"
$FrontendUrl = "http://localhost:$FrontendPort/"

Invoke-Logged "Starting TrendPulse backend and frontend..." {
    $BackendCommand = @"
`$env:DATABASE_URL='sqlite:///$DbPath'
`$env:API_KEY='dev_secret_key_123'
Set-Location '$BackendDir'
& '$PythonExe' seed.py
& '$PythonExe' -m uvicorn app.main:app --reload --host 127.0.0.1 --port $BackendPort
"@

    $FrontendCommand = @"
`$env:VITE_API_URL='$ApiUrl'
`$env:VITE_API_KEY='dev_secret_key_123'
Set-Location '$FrontendDir'
node '$ViteScript' --host localhost --port $FrontendPort --strictPort
"@

    Start-Process powershell.exe -ArgumentList @("-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $BackendCommand) -WorkingDirectory $BackendDir
    Start-Process powershell.exe -ArgumentList @("-NoProfile", "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $FrontendCommand) -WorkingDirectory $FrontendDir
}

Start-Sleep -Seconds 5
Start-Process $FrontendUrl

Write-Host ""
Write-Host "TrendPulse is starting locally." -ForegroundColor Green
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend:  $ApiUrl/docs"
Write-Host ""
