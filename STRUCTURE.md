# Project Structure

## Overview

Chimera Analytics is organized as a monorepo with multiple packages for different components of the system.

## Directory Structure

```
chimera-analytics/
├── packages/
│   ├── agents/                      # Python AI Agents
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   └── config.py           # Configuration management
│   │   ├── tests/
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── pyproject.toml          # Python tooling config
│   │   └── package.json
│   ├── api/                         # REST API & WebSocket Server
│   │   ├── src/
│   │   │   ├── index.ts            # Server entry point
│   │   │   └── config.ts           # Configuration management
│   │   ├── tsconfig.json           # TypeScript config
│   │   ├── .eslintrc.json          # ESLint config
│   │   ├── .prettierrc.json        # Prettier config
│   │   └── package.json
│   ├── sdk/                         # Client SDK
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── client.ts           # API client
│   │   │   └── types.ts            # Type definitions
│   │   ├── tsconfig.json
│   │   └── package.json
│   └── dashboard/                   # React Web Dashboard
│       ├── src/
│       │   ├── main.tsx            # Entry point
│       │   ├── App.tsx             # Root component
│       │   └── index.css           # Global styles
│       ├── index.html
│       ├── vite.config.ts          # Vite config
│       ├── tailwind.config.js      # Tailwind config
│       ├── tsconfig.json
│       └── package.json
├── scripts/
│   ├── setup.sh                     # Unix setup script
│   └── setup.ps1                    # Windows setup script
├── docker-compose.yml               # Local dev infrastructure
├── .env.example                     # Environment template
├── .gitignore
├── package.json                     # Monorepo root
├── Makefile                         # Common commands
├── README.md                        # Getting started guide
└── STRUCTURE.md                     # This file
```

## Package Details

### packages/agents

Python-based AI agents that handle:
- Natural language query processing
- Data retrieval from multiple sources
- Statistical analysis and pattern detection
- Report generation with LLMs
- Fact-checking and verification
- Follow-up question suggestions
- Continuous monitoring and alerting

**Key Technologies:**
- Python 3.11+
- Pydantic for configuration and validation
- spaCy/Transformers for NLP
- LangChain for LLM orchestration
- Pika for RabbitMQ communication

### packages/api

Node.js/TypeScript REST API and WebSocket server that:
- Provides HTTP endpoints for client applications
- Manages WebSocket connections for real-time updates
- Handles authentication and authorization
- Routes requests to appropriate agents via message bus
- Serves as the main interface layer

**Key Technologies:**
- Node.js 18+
- Express for REST API
- Socket.io for WebSocket
- Zod for validation
- TypeScript for type safety

### packages/sdk

TypeScript client SDK that:
- Provides programmatic access to the API
- Handles authentication
- Manages WebSocket connections
- Offers type-safe interfaces

**Key Technologies:**
- TypeScript
- Axios for HTTP requests
- Socket.io-client for WebSocket

### packages/dashboard

React web application that:
- Provides user interface for queries
- Displays reports and visualizations
- Manages dashboards and widgets
- Configures alerts and monitoring
- Shows real-time updates

**Key Technologies:**
- React 18
- TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Recharts for visualizations
- Zustand for state management

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

1. **Setup**: Run `scripts/setup.sh` (Unix) or `scripts/setup.ps1` (Windows)
2. **Start Infrastructure**: `docker-compose up -d`
3. **Start API**: `npm run dev:api`
4. **Start Dashboard**: `npm run dev:dashboard`
5. **Run Agents**: (Coming in future tasks)

## Build and Deployment

- **Development**: Hot-reload enabled for all packages
- **Production Build**: `npm run build` compiles all packages
- **Docker**: Dockerfiles will be added in deployment tasks
- **Kubernetes**: Helm charts will be added in deployment tasks

## Testing

- **Unit Tests**: Each package has its own test suite
- **Integration Tests**: Will be added in testing tasks
- **E2E Tests**: Will be added in testing tasks

## Code Quality

- **Linting**: ESLint (TypeScript), Pylint (Python)
- **Formatting**: Prettier (TypeScript), Black (Python)
- **Type Checking**: TypeScript compiler, mypy (Python)
- **Pre-commit Hooks**: (To be configured)

## Monorepo Management

- **Workspaces**: npm workspaces for package management
- **Shared Dependencies**: Hoisted to root when possible
- **Independent Versioning**: Each package has its own version
- **Build Order**: Handled automatically by npm workspaces
