#!/bin/bash

set -e

echo "🔍 Verifying Chimera Analytics setup..."

# Check if Docker services are running
echo "📦 Checking Docker services..."
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Docker services are not running. Run 'docker-compose up -d' first."
    exit 1
fi

# Check RabbitMQ
echo "🐰 Checking RabbitMQ..."
if curl -s -u guest:guest http://localhost:15672/api/overview > /dev/null; then
    echo "✅ RabbitMQ is running"
else
    echo "❌ RabbitMQ is not accessible"
    exit 1
fi

# Check InfluxDB
echo "📊 Checking InfluxDB..."
if curl -s http://localhost:8086/health > /dev/null; then
    echo "✅ InfluxDB is running"
else
    echo "❌ InfluxDB is not accessible"
    exit 1
fi

# Check MongoDB
echo "🍃 Checking MongoDB..."
if docker exec chimera-mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB is not accessible"
    exit 1
fi

# Check Redis
echo "🔴 Checking Redis..."
if docker exec chimera-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not accessible"
    exit 1
fi

# Check MinIO
echo "📦 Checking MinIO..."
if curl -s http://localhost:9000/minio/health/live > /dev/null; then
    echo "✅ MinIO is running"
else
    echo "❌ MinIO is not accessible"
    exit 1
fi

echo ""
echo "✅ All infrastructure services are running correctly!"
echo ""
echo "Service Status:"
docker-compose ps
