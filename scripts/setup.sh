#!/bin/bash

set -e

echo "🚀 Setting up Chimera Analytics..."

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Copy environment files
echo "📝 Setting up environment files..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env"
fi

if [ ! -f packages/agents/.env ]; then
    cp packages/agents/.env.example packages/agents/.env
    echo "✅ Created packages/agents/.env"
fi

if [ ! -f packages/api/.env ]; then
    cp packages/api/.env.example packages/api/.env
    echo "✅ Created packages/api/.env"
fi

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

echo "📦 Installing Python dependencies..."
cd packages/agents
pip install -r requirements.txt
cd ../..

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env files with your API keys and configuration"
echo "  2. Run 'npm run dev:api' to start the API server"
echo "  3. Run 'npm run dev:dashboard' to start the dashboard"
echo ""
echo "Service URLs:"
echo "  - API: http://localhost:3000"
echo "  - Dashboard: http://localhost:5173"
echo "  - RabbitMQ Management: http://localhost:15672"
echo "  - InfluxDB: http://localhost:8086"
echo "  - MinIO Console: http://localhost:9001"
