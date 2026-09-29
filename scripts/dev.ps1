# SAMUDRA-AI / ORCA — One-Command Local Development Starter
# ============================================================
# Usage: .\scripts\dev.ps1
# This script starts the entire SAMUDRA-AI platform locally.

param(
    [switch]$SkipDocker,
    [switch]$SkipSeed,
    [switch]$ApiOnly,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
SAMUDRA-AI Dev Starter
Usage: .\scripts\dev.ps1 [options]

Options:
  -SkipDocker   Skip Docker Compose startup (if services already running)
  -SkipSeed     Skip demo data seeding
  -ApiOnly      Start API only, not the React frontend
  -Help         Show this help

Services started:
  - PostgreSQL + PostGIS (port 5432) via Docker
  - Redis 7 (port 6379) via Docker
  - FastAPI API (port 8000) — http://localhost:8000
  - React dev server (port 5173) — http://localhost:5173
"@
    exit 0
}

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   SAMUDRA-AI / ORCA Marine Intelligence Platform ║" -ForegroundColor Cyan
Write-Host "  ║   Team Bytecrats | SIH 2026 | PS: SIH26176      ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ---- Check .env ------------------------------------------------
$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "⚠️  .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item (Join-Path $ProjectRoot ".env.example") $EnvFile
    Write-Host "✅ Created .env — edit it to add your LLM_API_KEY" -ForegroundColor Green
}

# ---- Docker (PostgreSQL + Redis) --------------------------------
if (-not $SkipDocker) {
    $DockerComposeFile = Join-Path $ProjectRoot "infra\docker-compose.yml"
    Write-Host "🐳 Starting Docker services (PostgreSQL + Redis)..." -ForegroundColor Blue

    $dockerCheck = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $dockerCheck) {
        Write-Host "⚠️  Docker not found. Please install Docker Desktop." -ForegroundColor Yellow
        Write-Host "   Using local PostgreSQL/Redis if already running." -ForegroundColor Yellow
    } else {
        docker compose -f $DockerComposeFile up -d
        Write-Host "✅ Docker services started" -ForegroundColor Green
        Start-Sleep -Seconds 5  # Wait for DB to be ready
    }
}

# ---- Python dependencies ----------------------------------------
$ApiDir = Join-Path $ProjectRoot "apps\api"
$ReqFile = Join-Path $ApiDir "requirements.txt"

Write-Host "🐍 Installing Python dependencies..." -ForegroundColor Blue
Set-Location $ApiDir

# Check for existing venv
$VenvPath = Join-Path $ProjectRoot ".venv"
if (-not (Test-Path $VenvPath)) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Gray
    python -m venv $VenvPath
}

# Activate venv
$ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    & $ActivateScript
}

python -m pip install --upgrade pip --quiet
python -m pip install -r $ReqFile --quiet
Write-Host "✅ Python dependencies installed" -ForegroundColor Green

# ---- Run Migrations ---------------------------------------------
Write-Host "🗃️  Running database setup..." -ForegroundColor Blue
Set-Location $ProjectRoot
$env:PYTHONPATH = "$ApiDir;$(Join-Path $ProjectRoot 'packages\shared-types')"

python -c @"
import asyncio, sys
sys.path.insert(0, 'apps/api')
sys.path.insert(0, 'packages/shared-types')
from core.database import engine
from core.db_models import Base

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print('Tables created successfully')

asyncio.run(create_tables())
"@ 2>&1
Write-Host "✅ Database tables ready" -ForegroundColor Green

# ---- Seed demo data ---------------------------------------------
if (-not $SkipSeed) {
    Write-Host "🌱 Seeding demo data..." -ForegroundColor Blue
    python scripts\seed_db.py
}

# ---- Start API --------------------------------------------------
Write-Host ""
Write-Host "🚀 Starting SAMUDRA-AI API on http://localhost:8000" -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "   Health:   http://localhost:8000/api/v1/health" -ForegroundColor Cyan

$env:PYTHONPATH = "$(Join-Path $ProjectRoot 'apps\api');$(Join-Path $ProjectRoot 'packages\shared-types')"
Set-Location $ApiDir

if ($ApiOnly) {
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
} else {
    # Start API in background
    $apiPath = Join-Path $ProjectRoot 'apps\api'
    $sharedPath = Join-Path $ProjectRoot 'packages\shared-types'
    $cmdString = "cd '$ApiDir'; `$env:PYTHONPATH = '$apiPath;$sharedPath'; python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    Start-Process -NoNewWindow powershell -ArgumentList "-Command", $cmdString

    # ---- Start Web Frontend -------------------------------------
    $WebDir = Join-Path $ProjectRoot "apps\web"
    if (Test-Path (Join-Path $WebDir "package.json")) {
        Write-Host ""
        Write-Host "🌐 Starting React frontend on http://localhost:5173" -ForegroundColor Green
        Set-Location $WebDir
        npm install --silent
        npm run dev
    } else {
        Write-Host ""
        Write-Host "ℹ️  React frontend not yet initialized (Phase 7+)" -ForegroundColor Yellow
        Write-Host "   API is running at http://localhost:8000" -ForegroundColor Cyan

        # Keep running the API in foreground
        Set-Location $ApiDir
        python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    }
}
