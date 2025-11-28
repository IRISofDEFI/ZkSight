#!/bin/bash

# Chimera Analytics - Development Startup Script

echo "🚀 Starting Chimera Analytics Development Environment"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Start infrastructure services
echo "📦 Starting infrastructure services (MongoDB, RabbitMQ, Redis, etc.)..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."

# Check MongoDB
if docker-compose ps mongodb | grep -q "Up"; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB failed to start"
fi

# Check RabbitMQ
if docker-compose ps rabbitmq | grep -q "Up"; then
    echo "✅ RabbitMQ is running"
else
    echo "❌ RabbitMQ failed to start"
fi

# Check Redis
if docker-compose ps redis | grep -q "Up"; then
    echo "✅ Redis is running"
else
    echo "❌ Redis failed to start"
fi

# Check InfluxDB
if docker-compose ps influxdb | grep -q "Up"; then
    echo "✅ InfluxDB is running"
else
    echo "❌ InfluxDB failed to start"
fi

echo ""
echo "🎉 Infrastructure services are ready!"
echo ""
echo "📝 Next steps:"
echo "   1. Start API server:  npm run dev:api"
echo "   2. Start dashboard:   npm run dev"
echo "   Or run both:          npm run dev:all"
echo ""
echo "🌐 Access points:"
echo "   Dashboard:    http://localhost:3000"
echo "   API Server:   http://localhost:3001"
echo "   RabbitMQ UI:  http://localhost:15672 (guest/guest)"
echo "   Grafana:      http://localhost:3002 (admin/admin)"
echo "   Jaeger:       http://localhost:16686"
echo ""
