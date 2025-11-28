# Project Structure

## Overview

Chimera Analytics is a multi-agent analytics platform for Zcash data analysis. The project uses a monorepo structure with the Next.js dashboard at the root and backend services in packages.

## Directory Structure

```
chimera-analytics/
├── packages/
│   ├── dashboard/                   # Next.js Web Dashboard
│   │   ├── src/
│   │   │   ├── app/                 # App Router pages
│   │   │   │   ├── dashboard/       # Main dashboard
│   │   │   │   ├── dashboard-builder/ # Dashboard builder
│   │   │   │   ├── query/           # Query interface
│   │   │   │   ├── report/[id]/     # Report viewer
│   │   │   │   ├── alerts/          # Alert management
│   │   │   │   ├── agents/          # Agent monitoring
│   │   │   │   ├── reports/         # Reports list
│   │   │   │   ├── settings/        # Settings
│   │   │   │   ├── login/           # Authentication
│   │   │   │   ├── signup/          # Registration
│   │   │   │   ├── mfa/             # Two-factor auth
│   │   │   │   └── api/             # API routes
│   │   │   ├── components/          # React components
│   │   │   │   ├── ui/              # Radix UI components
│   │   │   │   ├── sidebar.tsx      # Navigation
│   │   │   │   └── header.tsx       # Header
│   │   │   └── lib/                 # Utilities
│   │   │       ├── store.ts         # Zustand state
│   │   │       ├── websocket.tsx    # WebSocket provider
│   │   │       └── api.ts           # API client
│   │   ├── public/                  # Static assets
│   │   ├── next.config.ts           # Next.js config
│   │   ├── tailwind.config.js       # Tailwind config
│   │   ├── tsconfig.json            # TypeScript config
│   │   └── package.json
│   ├── agents/                      # Python AI Agents
│   │   ├── src/                     # Agent implementations
│   │   ├── tests/                   # Python tests
│   │   ├── requirements.txt         # Dependencies
│   │   └── pyproject.toml           # Python config
│   ├── api/                         # REST API & WebSocket Server
│   │   ├── src/                     # API implementation
│   │   ├── tsconfig.json            # TypeScript config
│   │   └── package.json
│   ├── sdk/                         # TypeScript Client SDK
│   │   ├── src/                     # SDK implementation
│   │   └── package.json
│   └── python-sdk/                  # Python Client SDK
│       ├── src/                     # SDK implementation
│       └── pyproject.toml
├── scripts/                         # Setup scripts
│   ├── setup.sh                     # Unix setup
│   └── setup.ps1                    # Windows setup
├── .kiro/                           # Kiro IDE config
│   └── specs/chimera-analytics/     # Spec documents
│       ├── requirements.md          # Requirements
│       ├── design.md                # Design doc
│       ├── tasks.md                 # Implementation tasks
│       └── STATUS.md                # Current status
├── docker-compose.yml               # Infrastructure services
├── .env.example                     # Environment template
├── package.json                     # Root package (workspaces)
├── README.md                        # Getting started
└── STRUCTURE.md                     # This file
```

## Component Details

### Dashboard (packages/dashboard/)

Next.js 15 web application with:
- **Authentication**: NextAuth with OAuth (Google, GitHub)
- **Query Interface**: Natural language query input
- **Dashboard Builder**: Customizable widget-based dashboards
- **Alert Management**: Rule builder and alert history
- **Report Viewer**: Analysis results with visualizations
- **Real-time Updates**: WebSocket integration

**Key Technologies:**
- Next.js 15 (App Router)
- React 18 + TypeScript
- TailwindCSS + Radix UI
- Recharts for visualizations
- Zustand for state management
- NextAuth for authentication

### AI Agents (packages/agents/)

Python-based agents:
- **Query Agent**: NLP query processing
- **Data Retrieval Agent**: Blockchain and API data fetching
- **Analysis Agent**: Statistical analysis and pattern detection
- **Narrative Agent**: Report generation with LLMs
- **Fact-Checker Agent**: Data verification
- **Follow-up Agent**: Question suggestions
- **Monitoring Agent**: Continuous monitoring and alerts

**Key Technologies:**
- Python 3.11+
- LangChain for LLM orchestration
- spaCy/Transformers for NLP
- Pika for RabbitMQ

### API Server (packages/api/)

Backend services:
- REST API endpoints
- WebSocket server for real-time updates
- Authentication and authorization
- Message bus integration
- Database operations

**Key Technologies:**
- Node.js 18+ + TypeScript
- Express for REST API
- Socket.io for WebSocket
- MongoDB for data storage

### SDKs (packages/sdk/, packages/python-sdk/)

Client libraries for programmatic access:
- TypeScript SDK for Node.js/browser
- Python SDK for Python applications
- Type-safe interfaces
- Authentication handling

## Infrastructure Services

### RabbitMQ
- **Purpose**: Message bus for agent communication
- **Ports**: 5672 (AMQP), 15672 (Management UI)
- **Default Credentials**: guest/guest

### InfluxDB
- **Purpose**: Time series database for metrics
- **Port**: 8086
- **Default Credentials**: admin/adminpassword
- **Organization**: chimera
- **Bucket**: zcash_metrics

### MongoDB
- **Purpose**: Document store for reports, configs, and metadata
- **Port**: 27017
- **Default Credentials**: admin/adminpassword
- **Database**: chimera

### Redis
- **Purpose**: Cache and session storage
- **Port**: 6379
- **Default Password**: (none in development)

### MinIO
- **Purpose**: S3-compatible object storage for files
- **Ports**: 9000 (API), 9001 (Console)
- **Default Credentials**: minioadmin/minioadmin

## Configuration

### Environment Variables

Each package has its own `.env` file:
- Root `.env`: Shared configuration
- `packages/agents/.env`: Python agent configuration
- `packages/api/.env`: API server configuration

Use the `.env.example` files as templates.

### Configuration Management

- **Python Agents**: Uses Pydantic Settings with validation
- **API Server**: Uses Zod for schema validation
- **Environment-specific**: Supports development, staging, production

## Development Workflow

### Quick Start
```bash
# 1. Install dependencies
npm install

# 2. Start infrastructure services
docker-compose up -d

# 3. Start dashboard (development)
npm run dev

# 4. Access dashboard
# http://localhost:3000
```

### Development Commands
```bash
npm run dev              # Start Next.js dashboard
npm run dev:api          # Start API server (when ready)
npm run build            # Build for production
npm run lint             # Run ESLint
npm run format           # Format with Prettier
```

### Infrastructure Services

**RabbitMQ** (Message Bus)
- Port: 5672 (AMQP), 15672 (Management UI)
- Credentials: guest/guest

**InfluxDB** (Time Series DB)
- Port: 8086
- Credentials: admin/adminpassword

**MongoDB** (Document Store)
- Port: 27017
- Credentials: admin/adminpassword

**Redis** (Cache)
- Port: 6379

**MinIO** (Object Storage)
- Port: 9000 (API), 9001 (Console)
- Credentials: minioadmin/minioadmin

## Project Status

### Completed (✅)
- Dashboard UI (81% complete)
- Authentication system
- Query interface
- Report viewer
- Alert management UI
- Dashboard builder UI
- WebSocket provider

### In Progress (🚧)
- AI agent implementations
- API server
- Real-time data integration
- Database persistence

### Planned (📋)
- Drag-and-drop dashboard
- Real MFA implementation
- Report export (PDF/HTML/JSON)
- Agent-to-agent communication
