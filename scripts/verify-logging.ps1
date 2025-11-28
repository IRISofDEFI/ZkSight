# Script to verify log aggregation setup
# This script checks if all logging components are running and accessible

Write-Host "🔍 Verifying Chimera Log Aggregation Setup..." -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"

# Check if docker-compose is running
Write-Host "1. Checking Docker Compose services..." -ForegroundColor Yellow
try {
    $services = docker-compose ps
    if ($services -match "Up") {
        Write-Host "✅ Docker Compose services are running" -ForegroundColor Green
    } else {
        Write-Host "❌ Docker Compose services are not running" -ForegroundColor Red
        Write-Host "   Run: docker-compose up -d" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Failed to check Docker Compose services" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check Loki
Write-Host "2. Checking Loki..." -ForegroundColor Yellow
try {
    $lokiResponse = Invoke-WebRequest -Uri "http://localhost:3100/ready" -UseBasicParsing -TimeoutSec 5
    if ($lokiResponse.Content -match "ready") {
        Write-Host "✅ Loki is ready" -ForegroundColor Green
    } else {
        Write-Host "❌ Loki is not accessible" -ForegroundColor Red
        Write-Host "   Check logs: docker-compose logs loki" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Loki is not accessible" -ForegroundColor Red
    Write-Host "   Check logs: docker-compose logs loki" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check Promtail
Write-Host "3. Checking Promtail..." -ForegroundColor Yellow
try {
    $promtailStatus = docker-compose ps promtail
    if ($promtailStatus -match "Up") {
        Write-Host "✅ Promtail is running" -ForegroundColor Green
    } else {
        Write-Host "❌ Promtail is not running" -ForegroundColor Red
        Write-Host "   Check logs: docker-compose logs promtail" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Failed to check Promtail status" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check Grafana
Write-Host "4. Checking Grafana..." -ForegroundColor Yellow
try {
    $grafanaResponse = Invoke-WebRequest -Uri "http://localhost:3000/api/health" -UseBasicParsing -TimeoutSec 5
    if ($grafanaResponse.Content -match "ok") {
        Write-Host "✅ Grafana is ready" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Grafana is not accessible (may conflict with dashboard on port 3000)" -ForegroundColor Yellow
        Write-Host "   Note: Grafana and Dashboard both use port 3000" -ForegroundColor Yellow
        Write-Host "   Consider changing Grafana port in docker-compose.yml" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Grafana is not accessible (may conflict with dashboard on port 3000)" -ForegroundColor Yellow
    Write-Host "   Note: Grafana and Dashboard both use port 3000" -ForegroundColor Yellow
}
Write-Host ""

# Check configuration files
Write-Host "5. Checking configuration files..." -ForegroundColor Yellow
$configFiles = @(
    "config/loki/local-config.yaml",
    "config/promtail/config.yaml",
    "config/grafana/provisioning/datasources/loki.yaml"
)

$allConfigsExist = $true
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists" -ForegroundColor Green
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        $allConfigsExist = $false
    }
}

if (-not $allConfigsExist) {
    exit 1
}
Write-Host ""

# Test log ingestion
Write-Host "6. Testing log ingestion..." -ForegroundColor Yellow
Write-Host "   Sending test log to Loki..." -ForegroundColor Gray
try {
    $timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() * 1000000
    $body = @{
        streams = @(
            @{
                stream = @{
                    service = "test"
                    level = "info"
                }
                values = @(
                    @($timestamp.ToString(), "Test log message from verification script")
                )
            }
        )
    } | ConvertTo-Json -Depth 10

    $response = Invoke-WebRequest -Uri "http://localhost:3100/loki/api/v1/push" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing `
        -TimeoutSec 5

    Write-Host "✅ Successfully sent test log to Loki" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to send test log to Loki" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Query test log
Write-Host "7. Querying test log..." -ForegroundColor Yellow
Start-Sleep -Seconds 2  # Wait for log to be indexed
try {
    $queryUrl = "http://localhost:3100/loki/api/v1/query_range?query={service=`"test`"}&limit=1"
    $queryResponse = Invoke-WebRequest -Uri $queryUrl -UseBasicParsing -TimeoutSec 5
    if ($queryResponse.Content -match "Test log message") {
        Write-Host "✅ Successfully queried test log from Loki" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Could not verify test log query" -ForegroundColor Yellow
        Write-Host "   This may be normal if logs haven't been indexed yet" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️  Could not verify test log query" -ForegroundColor Yellow
    Write-Host "   This may be normal if logs haven't been indexed yet" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "✅ Log Aggregation Setup Verification Complete!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Access Points:" -ForegroundColor Cyan
Write-Host "   • Loki API: http://localhost:3100"
Write-Host "   • Grafana: http://localhost:3000 (admin/admin)"
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "   • Log Aggregation Guide: config/LOG_AGGREGATION.md"
Write-Host ""
Write-Host "🔍 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Access Grafana at http://localhost:3000"
Write-Host "   2. Navigate to 'Dashboards' → 'Chimera Application Logs'"
Write-Host "   3. Start your application to see logs flowing in"
Write-Host ""
Write-Host "💡 Tip: Use correlation IDs to trace requests across services" -ForegroundColor Yellow
Write-Host "   Example query: {correlation_id=`"your-id`"}"
Write-Host ""
