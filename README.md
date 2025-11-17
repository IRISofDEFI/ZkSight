# Chimera Multi-Agent Analytics System

A comprehensive multi-agent analytics platform for Zcash data analysis, providing natural language querying, automated insights, and real-time monitoring.

## Project Structure

```
chimera-analytics/
├── packages/
│   ├── agents/          # Python-based AI agents
│   ├── api/             # REST API and WebSocket server (Node.js/TypeScript)
│   ├── sdk/             # Client SDK (TypeScript)
│   └── dashboard/       # Web dashboard (React/TypeScript)
├── docker-compose.yml   # Local development environment
└── package.json         # Monorepo configuration
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker and Docker Compose
- Git

## Quick Start

### 1. Clone and Install Dependencies

```bash
# Install Node.js dependencies
npm install

# Install Python dependencies for agents
cd packages/agents
pip install -r requirements.txt
cd ../..
```

### 2. Configure Environment

```bash
# Copy environment files
cp .env.example .env
cp packages/agents/.env.example packages/agents/.env
cp packages/api/.env.example packages/api/.env

# Edit .env files with your configuration
```

### 3. Start Infrastructure Services

```bash
# Start databases, message bus, and cache
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 4. Run Development Servers

```bash
# Terminal 1: Start API server
npm run dev:api

# Terminal 2: Start dashboard
npm run dev:dashboard
```

## Infrastructure Services

The Docker Compose setup includes:

- **RabbitMQ** (ports 5672, 15672): Message bus for agent communication
- **InfluxDB** (port 8086): Time series database for metrics
- **MongoDB** (port 27017): Document store for reports and configurations
- **Redis** (port 6379): Cache and session storage
- **MinIO** (ports 9000, 9001): S3-compatible object storage

### Service URLs

- RabbitMQ Management: http://localhost:15672 (guest/guest)
- InfluxDB UI: http://localhost:8086 (admin/adminpassword)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)
- API Server: http://localhost:3000
- Dashboard: http://localhost:5173

## Development

### Code Quality

```bash
# Lint all packages
npm run lint

# Format all packages
npm run format

# Run tests
npm run test
```

### Python Agents

```bash
cd packages/agents

# Lint
pylint src/

# Format
black src/ && isort src/

# Type check
mypy src/

# Run tests
pytest
```

### TypeScript Packages

```bash
# API
cd packages/api
npm run lint
npm run format
npm test

# SDK
cd packages/sdk
npm run lint
npm run build

# Dashboard
cd packages/dashboard
npm run lint
npm run build
```

## Building for Production

```bash
# Build all packages
npm run build

# Build Docker images (coming soon)
# docker build -t chimera-api -f packages/api/Dockerfile .
# docker build -t chimera-agents -f packages/agents/Dockerfile .
```

## Architecture

The system follows a microservices architecture with event-driven communication:

1. **Interface Layer**: Web dashboard, REST API, WebSocket server, Client SDK
2. **Agent Layer**: Specialized AI agents (Query, Data Retrieval, Analysis, Narrative, Fact-Checker, Follow-up, Monitoring)
3. **Message Bus**: RabbitMQ for asynchronous agent communication
4. **Data Layer**: InfluxDB (time series), MongoDB (documents), Redis (cache), MinIO (objects)

## Documentation

- [Requirements](/.kiro/specs/chimera-analytics/requirements.md)
- [Design](/.kiro/specs/chimera-analytics/design.md)
- [Implementation Tasks](/.kiro/specs/chimera-analytics/tasks.md)

## License

Proprietary
