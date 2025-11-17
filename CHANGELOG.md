# Changelog

All notable changes to the Chimera Analytics project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure with monorepo setup
- Package scaffolding for agents, API, SDK, and dashboard
- Docker Compose configuration for local development
- Configuration management with validation for all packages
- Development tooling (linting, formatting, testing)
- Setup scripts for Unix/Mac and Windows
- Verification scripts for infrastructure services
- Comprehensive documentation (README, STRUCTURE, CONTRIBUTING)
- Environment configuration templates

### Infrastructure
- RabbitMQ for message bus (ports 5672, 15672)
- InfluxDB for time series data (port 8086)
- MongoDB for document storage (port 27017)
- Redis for caching (port 6379)
- MinIO for object storage (ports 9000, 9001)

### Packages
- `@chimera/agents`: Python-based AI agents package
- `@chimera/api`: REST API and WebSocket server
- `@chimera/sdk`: TypeScript client SDK
- `@chimera/dashboard`: React web dashboard

## [1.0.0] - TBD

Initial release (planned)
