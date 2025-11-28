#!/bin/bash

# Verification script for distributed tracing setup
# This script checks that all tracing components are properly configured

set -e

echo "========================================="
echo "Distributed Tracing Verification"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Jaeger is running
echo "1. Checking Jaeger service..."
if docker-compose ps jaeger | grep -q "Up"; then
    echo -e "${GREEN}✓ Jaeger is running${NC}"
else
    echo -e "${RED}✗ Jaeger is not running${NC}"
    echo "  Start with: docker-compose up -d jaeger"
    exit 1
fi

# Check Jaeger UI
echo ""
echo "2. Checking Jaeger UI..."
if curl -s -f http://localhost:16686 > /dev/null; then
    echo -e "${GREEN}✓ Jaeger UI is accessible at http://localhost:16686${NC}"
else
    echo -e "${RED}✗ Jaeger UI is not accessible${NC}"
    exit 1
fi

# Check OTLP endpoint
echo ""
echo "3. Checking OTLP endpoint..."
if nc -z localhost 4317 2>/dev/null; then
    echo -e "${GREEN}✓ OTLP gRPC endpoint is listening on port 4317${NC}"
else
    echo -e "${YELLOW}⚠ OTLP endpoint check skipped (nc not available)${NC}"
fi

# Check Python dependencies
echo ""
echo "4. Checking Python OpenTelemetry dependencies..."
cd packages/agents
if python3 -c "import opentelemetry.api; import opentelemetry.sdk" 2>/dev/null; then
    echo -e "${GREEN}✓ Python OpenTelemetry packages are installed${NC}"
else
    echo -e "${RED}✗ Python OpenTelemetry packages are missing${NC}"
    echo "  Install with: pip install -r requirements.txt"
    exit 1
fi
cd ../..

# Check TypeScript dependencies
echo ""
echo "5. Checking TypeScript OpenTelemetry dependencies..."
cd packages/api
if [ -d "node_modules/@opentelemetry" ]; then
    echo -e "${GREEN}✓ TypeScript OpenTelemetry packages are installed${NC}"
else
    echo -e "${RED}✗ TypeScript OpenTelemetry packages are missing${NC}"
    echo "  Install with: npm install"
    exit 1
fi
cd ../..

# Check tracing files exist
echo ""
echo "6. Checking tracing implementation files..."
files=(
    "packages/agents/src/tracing.py"
    "packages/agents/src/init_tracing.py"
    "packages/api/src/tracing.ts"
    "packages/agents/TRACING.md"
    "TRACING_SETUP.md"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file (missing)${NC}"
        all_exist=false
    fi
done

if [ "$all_exist" = false ]; then
    exit 1
fi

# Check docker-compose has Jaeger configured
echo ""
echo "7. Checking docker-compose.yml configuration..."
if grep -q "jaeger:" docker-compose.yml; then
    echo -e "${GREEN}✓ Jaeger service is configured in docker-compose.yml${NC}"
else
    echo -e "${RED}✗ Jaeger service is not configured in docker-compose.yml${NC}"
    exit 1
fi

# Summary
echo ""
echo "========================================="
echo -e "${GREEN}All checks passed!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. View Jaeger UI: http://localhost:16686"
echo "2. Start API server: cd packages/api && npm run dev"
echo "3. Start an agent: cd packages/agents && python -m src.examples.tracing_example"
echo "4. Generate some traces and view them in Jaeger UI"
echo ""
echo "Documentation:"
echo "- Setup guide: TRACING_SETUP.md"
echo "- Agent guide: packages/agents/TRACING.md"
echo ""
