# PowerShell verification script for Windows

Write-Host "🔍 Verifying Chimera Analytics setup..." -ForegroundColor Green

# Check if Docker services are running
Write-Host "📦 Checking Docker services..." -ForegroundColor Yellow
$dockerStatus = docker-compose ps
if (-not $dockerStatus) {
    Write-Host "⚠️  Docker services are not running. Run 'docker-compose up -d' first." -ForegroundColor Yellow
    exit 1
}

# Check RabbitMQ
Write-Host "🐰 Checking RabbitMQ..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:15672/api/overview" -UseBasicParsing -Credential (New-Object System.Management.Automation.PSCredential("guest", (ConvertTo-SecureString "guest" -AsPlainText -Force))) -ErrorAction Stop
    Write-Host "✅ RabbitMQ is running" -ForegroundColor Green
} catch {
    Write-Host "❌ RabbitMQ is not accessible" -ForegroundColor Red
    exit 1
}

# Check InfluxDB
Write-Host "📊 Checking InfluxDB..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8086/health" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ InfluxDB is running" -ForegroundColor Green
} catch {
    Write-Host "❌ InfluxDB is not accessible" -ForegroundColor Red
    exit 1
}

# Check MongoDB
Write-Host "🍃 Checking MongoDB..." -ForegroundColor Yellow
try {
    $result = docker exec chimera-mongodb mongosh --eval "db.adminCommand('ping')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ MongoDB is running" -ForegroundColor Green
    } else {
        throw "MongoDB check failed"
    }
} catch {
    Write-Host "❌ MongoDB is not accessible" -ForegroundColor Red
    exit 1
}

# Check Redis
Write-Host "🔴 Checking Redis..." -ForegroundColor Yellow
try {
    $result = docker exec chimera-redis redis-cli ping 2>&1
    if ($result -match "PONG") {
        Write-Host "✅ Redis is running" -ForegroundColor Green
    } else {
        throw "Redis check failed"
    }
} catch {
    Write-Host "❌ Redis is not accessible" -ForegroundColor Red
    exit 1
}

# Check MinIO
Write-Host "📦 Checking MinIO..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9000/minio/health/live" -UseBasicParsing -ErrorAction Stop
    Write-Host "✅ MinIO is running" -ForegroundColor Green
} catch {
    Write-Host "❌ MinIO is not accessible" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ All infrastructure services are running correctly!" -ForegroundColor Green
Write-Host ""
Write-Host "Service Status:" -ForegroundColor Cyan
docker-compose ps
