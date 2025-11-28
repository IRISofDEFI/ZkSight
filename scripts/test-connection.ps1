# Test Frontend-Backend Connection

Write-Host "🔍 Testing Chimera Analytics Connections" -ForegroundColor Cyan
Write-Host ""

# Test API Health
Write-Host "Testing API Server..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ API Server is responding" -ForegroundColor Green
        $content = $response.Content | ConvertFrom-Json
        Write-Host "   Status: $($content.status)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ API Server is not responding" -ForegroundColor Red
    Write-Host "   Make sure to run: npm run dev:api" -ForegroundColor Yellow
}

Write-Host ""

# Test MongoDB
Write-Host "Testing MongoDB..." -ForegroundColor Yellow
try {
    $mongoTest = docker exec chimera-mongodb mongosh --quiet --eval "db.adminCommand('ping')" 2>&1
    if ($mongoTest -match "ok") {
        Write-Host "✅ MongoDB is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ MongoDB is not accessible" -ForegroundColor Red
}

Write-Host ""

# Test Redis
Write-Host "Testing Redis..." -ForegroundColor Yellow
try {
    $redisTest = docker exec chimera-redis redis-cli ping 2>&1
    if ($redisTest -match "PONG") {
        Write-Host "✅ Redis is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ Redis is not accessible" -ForegroundColor Red
}

Write-Host ""

# Test RabbitMQ
Write-Host "Testing RabbitMQ..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:15672/api/overview" -UseBasicParsing -Credential (New-Object System.Management.Automation.PSCredential("guest", (ConvertTo-SecureString "guest" -AsPlainText -Force)))
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ RabbitMQ is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ RabbitMQ is not accessible" -ForegroundColor Red
}

Write-Host ""

# Test InfluxDB
Write-Host "Testing InfluxDB..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8086/health" -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ InfluxDB is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ InfluxDB is not accessible" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎯 Connection Test Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "If API Server is not responding:" -ForegroundColor Yellow
Write-Host "   Run: npm run dev:api" -ForegroundColor White
Write-Host ""
Write-Host "If Dashboard is not running:" -ForegroundColor Yellow
Write-Host "   Run: npm run dev" -ForegroundColor White
Write-Host ""
