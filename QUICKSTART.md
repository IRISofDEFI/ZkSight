# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Prerequisites Check

Ensure you have installed:
- Node.js 18+ (`node --version`)
- Python 3.11+ (`python --version`)
- Docker Desktop (`docker --version`)

### 2. Automated Setup

**On Unix/Mac:**
```bash
bash scripts/setup.sh
```

**On Windows:**
```powershell
powershell scripts/setup.ps1
```

This script will:
- ✅ Check prerequisites
- ✅ Copy environment files
- ✅ Install dependencies
- ✅ Start Docker services

### 3. Verify Installation

**On Unix/Mac:**
```bash
bash scripts/verify-setup.sh
```

**On Windows:**
```powershell
powershell scripts/verify-setup.ps1
```

### 4. Configure API Keys (Optional)

Edit the `.env` files to add your API keys:
- `.env` - Root configuration
- `packages/agents/.env` - Agent configuration
- `packages/api/.env` - API configuration

Required for full functionality:
- OpenAI API key (for LLM features)
- Exchange API keys (for market data)
- Social API keys (for sentiment analysis)

### 5. Start Development Servers

**Terminal 1 - API Server:**
```bash
npm run dev:api
```

**Terminal 2 - Dashboard:**
```bash
npm run dev:dashboard
```

### 6. Access the Application

- **Dashboard**: http://localhost:5173
- **API**: http://localhost:3000
- **API Health**: http://localhost:3000/health

### 7. Access Infrastructure UIs

- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **InfluxDB**: http://localhost:8086 (admin/adminpassword)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Common Commands

### Development
```bash
# Start all infrastructure
docker-compose up -d

# Stop all infrastructure
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart rabbitmq
```

### Code Quality
```bash
# Lint all code
npm run lint

# Format all code
npm run format

# Run all tests
npm run test
```

### Package Management
```bash
# Install new dependency in API
npm install <package> --workspace=@chimera/api

# Install new dependency in dashboard
npm install <package> --workspace=@chimera/dashboard

# Install Python dependency
cd packages/agents && pip install <package>
```

## Troubleshooting

### Docker Services Won't Start

```bash
# Check if ports are already in use
netstat -an | grep 5672  # RabbitMQ
netstat -an | grep 8086  # InfluxDB
netstat -an | grep 27017 # MongoDB
netstat -an | grep 6379  # Redis

# Stop conflicting services or change ports in docker-compose.yml
```

### API Server Won't Start

```bash
# Check if port 3000 is available
netstat -an | grep 3000

# Check environment configuration
cat packages/api/.env

# View detailed logs
npm run dev:api
```

### Dashboard Won't Start

```bash
# Check if port 5173 is available
netstat -an | grep 5173

# Clear cache and reinstall
rm -rf node_modules packages/dashboard/node_modules
npm install
```

### Python Dependencies Issues

```bash
# Create virtual environment
cd packages/agents
python -m venv venv
source venv/bin/activate  # Unix/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Next Steps

1. **Explore the codebase**: Review the [STRUCTURE.md](STRUCTURE.md) document
2. **Read the design**: Check `.kiro/specs/chimera-analytics/design.md`
3. **Start implementing**: Follow tasks in `.kiro/specs/chimera-analytics/tasks.md`
4. **Contribute**: Read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [STRUCTURE.md](STRUCTURE.md) for architecture details
- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check the design documents in `.kiro/specs/chimera-analytics/`

## Development Workflow

1. Start infrastructure: `docker-compose up -d`
2. Verify services: `bash scripts/verify-setup.sh`
3. Start API: `npm run dev:api`
4. Start dashboard: `npm run dev:dashboard`
5. Make changes and test
6. Run linting: `npm run lint`
7. Run tests: `npm run test`
8. Commit and push

Happy coding! 🚀
