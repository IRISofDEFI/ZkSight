# Chimera Analytics

Multi-agent analytics platform for Zcash blockchain data analysis.

## Features

- 🤖 **7 Specialized AI Agents** - Query processing, data retrieval, analysis, narrative generation, fact-checking, follow-up suggestions, and monitoring
- 📊 **Interactive Dashboards** - Customizable widget-based dashboards with real-time updates
- 🔍 **Natural Language Queries** - Ask questions in plain English about Zcash network data
- 📈 **Advanced Analytics** - Statistical analysis, anomaly detection, pattern recognition
- 🔔 **Smart Alerts** - Configurable alert rules with multiple notification channels
- 📄 **Automated Reports** - AI-generated reports with visualizations and insights

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### Installation

```bash
# Clone repository
git clone <repository-url>
cd chimera-analytics

# Install dependencies
npm install

# Start infrastructure services
docker-compose up -d

# Start dashboard
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Default Login

```
Email: test@example.com
Password: password123
```

## Project Structure

```
chimera-analytics/
├── packages/
│   ├── dashboard/          # Next.js Dashboard
│   │   ├── src/app/        # Pages (dashboard, query, reports, alerts)
│   │   ├── src/components/ # React components
│   │   └── src/lib/        # Utilities (store, websocket, api)
│   ├── agents/             # Python AI agents
│   ├── api/                # REST API & WebSocket server
│   ├── sdk/                # TypeScript SDK
│   └── python-sdk/         # Python SDK
└── docker-compose.yml      # Infrastructure services
```

See [STRUCTURE.md](STRUCTURE.md) for detailed structure.

## Development

### Commands

```bash
npm run dev              # Start dashboard (port 3000)
npm run build            # Build for production
npm run lint             # Run linter
npm run format           # Format code
```

### Infrastructure Services

| Service | Port | Credentials |
|---------|------|-------------|
| Dashboard | 3000 | - |
| RabbitMQ | 5672, 15672 | guest/guest |
| InfluxDB | 8086 | admin/adminpassword |
| MongoDB | 27017 | admin/adminpassword |
| Redis | 6379 | - |
| MinIO | 9000, 9001 | minioadmin/minioadmin |

## Architecture

### Dashboard (Next.js 15)
- **Authentication**: NextAuth with OAuth (Google, GitHub)
- **State Management**: Zustand
- **Styling**: TailwindCSS + Radix UI
- **Charts**: Recharts
- **Real-time**: WebSocket provider

### AI Agents (Python)
1. **Query Agent** - Natural language processing
2. **Data Retrieval Agent** - Blockchain and API data
3. **Analysis Agent** - Statistical analysis
4. **Narrative Agent** - Report generation
5. **Fact-Checker Agent** - Data verification
6. **Follow-up Agent** - Question suggestions
7. **Monitoring Agent** - Continuous monitoring

### Backend (Node.js + TypeScript)
- REST API with Express
- WebSocket server with Socket.io
- Message bus integration (RabbitMQ)
- Database operations (MongoDB, InfluxDB)

## Configuration

Create `.env.local`:

```env
# NextAuth
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key

# OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_ID=your-github-client-id
GITHUB_SECRET=your-github-client-secret

# WebSocket
NEXT_PUBLIC_WS_URL=ws://localhost:3001

# API
NEXT_PUBLIC_API_URL=http://localhost:3001
```

## Current Status

### Completed ✅
- Dashboard UI (81%)
- Authentication system
- Query interface
- Report viewer
- Alert management
- Dashboard builder
- WebSocket integration

### In Progress 🚧
- AI agent implementations
- API server
- Real-time data integration
- Database persistence

### Planned 📋
- Drag-and-drop dashboard
- Real MFA implementation
- Report export (PDF/HTML/JSON)
- Agent communication

## Documentation

- [STRUCTURE.md](STRUCTURE.md) - Detailed project structure
- [.kiro/specs/chimera-analytics/](/.kiro/specs/chimera-analytics/) - Spec documents
  - [requirements.md](/.kiro/specs/chimera-analytics/requirements.md) - Requirements
  - [design.md](/.kiro/specs/chimera-analytics/design.md) - Architecture design
  - [tasks.md](/.kiro/specs/chimera-analytics/tasks.md) - Implementation tasks

## Tech Stack

**Frontend:**
- Next.js 15, React 18, TypeScript
- TailwindCSS, Radix UI, Recharts
- Zustand, NextAuth, Socket.io-client

**Backend:**
- Node.js, Express, Socket.io
- Python, LangChain, spaCy

**Infrastructure:**
- RabbitMQ, MongoDB, InfluxDB, Redis, MinIO
- Docker, Docker Compose

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
