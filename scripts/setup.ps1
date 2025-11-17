# PowerShell setup script for Windows

Write-Host "🚀 Setting up Chimera Analytics..." -ForegroundColor Green

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+ first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python is not installed. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Docker is not installed. Please install Docker first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Copy environment files
Write-Host "📝 Setting up environment files..." -ForegroundColor Yellow

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "✅ Created .env" -ForegroundColor Green
}

if (-not (Test-Path packages/agents/.env)) {
    Copy-Item packages/agents/.env.example packages/agents/.env
    Write-Host "✅ Created packages/agents/.env" -ForegroundColor Green
}

if (-not (Test-Path packages/api/.env)) {
    Copy-Item packages/api/.env.example packages/api/.env
    Write-Host "✅ Created packages/api/.env" -ForegroundColor Green
}

# Install dependencies
Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
npm install

Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
Set-Location packages/agents
pip install -r requirements.txt
Set-Location ../..

# Start Docker services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "🏥 Checking service health..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Edit .env files with your API keys and configuration"
Write-Host "  2. Run 'npm run dev:api' to start the API server"
Write-Host "  3. Run 'npm run dev:dashboard' to start the dashboard"
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  - API: http://localhost:3000"
Write-Host "  - Dashboard: http://localhost:5173"
Write-Host "  - RabbitMQ Management: http://localhost:15672"
Write-Host "  - InfluxDB: http://localhost:8086"
Write-Host "  - MinIO Console: http://localhost:9001"
