# Verification script for distributed tracing setup (PowerShell)
# This script checks that all tracing components are properly configured

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Distributed Tracing Verification" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

$allPassed = $true

# Check if Jaeger is running
Write-Host "1. Checking Jaeger service..."
$jaegerStatus = docker-compose ps jaeger 2>$null
if ($jaegerStatus -match "Up") {
    Write-Host "checkmark Jaeger is running" -ForegroundColor Green
} else {
    Write-Host "X Jaeger is not running" -ForegroundColor Red
    Write-Host "  Start with: docker-compose up -d jaeger" -ForegroundColor Yellow
    $allPassed = $false
}

# Check Jaeger UI
Write-Host ""
Write-Host "2. Checking Jaeger UI..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:16686" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "checkmark Jaeger UI is accessible at http://localhost:16686" -ForegroundColor Green
}
catch {
    Write-Host "X Jaeger UI is not accessible" -ForegroundColor Red
    $allPassed = $false
}

# Check OTLP endpoint
Write-Host ""
Write-Host "3. Checking OTLP endpoint..."
try {
    $tcpClient = New-Object System.Net.Sockets.TcpClient
    $tcpClient.Connect("localhost", 4317)
    Write-Host "checkmark OTLP gRPC endpoint is listening on port 4317" -ForegroundColor Green
    $tcpClient.Close()
}
catch {
    Write-Host "warning OTLP endpoint is not accessible (Jaeger may not be fully started)" -ForegroundColor Yellow
}

# Check Python dependencies
Write-Host ""
Write-Host "4. Checking Python OpenTelemetry dependencies..."
try {
    Push-Location packages/agents
    $null = python -c "import opentelemetry.api; import opentelemetry.sdk" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "checkmark Python OpenTelemetry packages are installed" -ForegroundColor Green
    }
    else {
        Write-Host "X Python OpenTelemetry packages are missing" -ForegroundColor Red
        Write-Host "  Install with: pip install -r requirements.txt" -ForegroundColor Yellow
        $allPassed = $false
    }
}
catch {
    Write-Host "warning Could not check Python dependencies" -ForegroundColor Yellow
}
finally {
    Pop-Location
}

# Check TypeScript dependencies
Write-Host ""
Write-Host "5. Checking TypeScript OpenTelemetry dependencies..."
try {
    Push-Location packages/api
    if (Test-Path "node_modules/@opentelemetry") {
        Write-Host "checkmark TypeScript OpenTelemetry packages are installed" -ForegroundColor Green
    }
    else {
        Write-Host "X TypeScript OpenTelemetry packages are missing" -ForegroundColor Red
        Write-Host "  Install with: npm install" -ForegroundColor Yellow
        $allPassed = $false
    }
}
finally {
    Pop-Location
}

# Check tracing files exist
Write-Host ""
Write-Host "6. Checking tracing implementation files..."
$files = @(
    "packages/agents/src/tracing.py",
    "packages/agents/src/init_tracing.py",
    "packages/api/src/tracing.ts",
    "packages/agents/TRACING.md",
    "TRACING_SETUP.md"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "checkmark $file" -ForegroundColor Green
    }
    else {
        Write-Host "X $file (missing)" -ForegroundColor Red
        $allPassed = $false
    }
}

# Check docker-compose has Jaeger configured
Write-Host ""
Write-Host "7. Checking docker-compose.yml configuration..."
$dockerCompose = Get-Content docker-compose.yml -Raw
if ($dockerCompose -match "jaeger:") {
    Write-Host "checkmark Jaeger service is configured in docker-compose.yml" -ForegroundColor Green
}
else {
    Write-Host "X Jaeger service is not configured in docker-compose.yml" -ForegroundColor Red
    $allPassed = $false
}

# Summary
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "All checks passed!" -ForegroundColor Green
}
else {
    Write-Host "Some checks failed!" -ForegroundColor Red
}
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. View Jaeger UI: http://localhost:16686"
Write-Host "2. Start API server: cd packages/api; npm run dev"
Write-Host "3. Start an agent: cd packages/agents; python -m src.examples.tracing_example"
Write-Host "4. Generate some traces and view them in Jaeger UI"
Write-Host ""
Write-Host "Documentation:"
Write-Host "- Setup guide: TRACING_SETUP.md"
Write-Host "- Agent guide: packages/agents/TRACING.md"
Write-Host ""

if (-not $allPassed) {
    exit 1
}
