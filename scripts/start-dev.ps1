# Chimera Analytics - Development Startup Script (PowerShell)

Write-Host "🚀 Starting Chimera Analytics Development Environment" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker first." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Start infrastructure services
Write-Host "📦 Starting infrastructure services (MongoDB, RabbitMQ, Redis, etc.)..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host ""
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

# Check MongoDB
$mongoStatus = docker-compose ps mongodb
if ($mongoStatus -match "Up") {
    Write-Host "✅ MongoDB is running" -ForegroundColor Green
} else {
    Write-Host "❌ MongoDB failed to start" -ForegroundColor Red
}

# Check RabbitMQ
$rabbitStatus = docker-compose ps rabbitmq
if ($rabbitStatus -match "Up") {
    Write-Host "✅ RabbitMQ is running" -ForegroundColor Green
} else {
    Write-Host "❌ RabbitMQ failed to start" -ForegroundColor Red
}

# Check Redis
$redisStatus = docker-compose ps redis
if ($redisStatus -match "Up") {
    Write-Host "✅ Redis is running" -ForegroundColor Green
} else {
    Write-Host "❌ Redis failed to start" -ForegroundColor Red
}

# Check InfluxDB
$influxStatus = docker-compose ps influxdb
if ($influxStatus -match "Up") {
    Write-Host "✅ InfluxDB is running" -ForegroundColor Green
} else {
    Write-Host "❌ InfluxDB failed to start" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 Infrastructure services are ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Start API server:  npm run dev:api"
Write-Host "   2. Start dashboard:   npm run dev"
Write-Host "   Or run both:          npm run dev:all"
Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "   Dashboard:    http://localhost:3000"
Write-Host "   API Server:   http://localhost:3001"
Write-Host "   RabbitMQ UI:  http://localhost:15672 (guest/guest)"
Write-Host "   Grafana:      http://localhost:3002 (admin/admin)"
Write-Host "   Jaeger:       http://localhost:16686"
Write-Host ""
