#!/bin/bash

# Script to verify log aggregation setup
# This script checks if all logging components are running and accessible

set -e

echo "🔍 Verifying Chimera Log Aggregation Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is running
echo "1. Checking Docker Compose services..."
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}❌ Docker Compose services are not running${NC}"
    echo "   Run: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose services are running${NC}"
echo ""

# Check Loki
echo "2. Checking Loki..."
if curl -s http://localhost:3100/ready | grep -q "ready"; then
    echo -e "${GREEN}✅ Loki is ready${NC}"
else
    echo -e "${RED}❌ Loki is not accessible${NC}"
    echo "   Check logs: docker-compose logs loki"
    exit 1
fi
echo ""

# Check Promtail
echo "3. Checking Promtail..."
if docker-compose ps promtail | grep -q "Up"; then
    echo -e "${GREEN}✅ Promtail is running${NC}"
else
    echo -e "${RED}❌ Promtail is not running${NC}"
    echo "   Check logs: docker-compose logs promtail"
    exit 1
fi
echo ""

# Check Grafana
echo "4. Checking Grafana..."
if curl -s http://localhost:3000/api/health | grep -q "ok"; then
    echo -e "${GREEN}✅ Grafana is ready${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana is not accessible (may conflict with dashboard on port 3000)${NC}"
    echo "   Note: Grafana and Dashboard both use port 3000"
    echo "   Consider changing Grafana port in docker-compose.yml"
fi
echo ""

# Check configuration files
echo "5. Checking configuration files..."
if [ -f "config/loki/local-config.yaml" ]; then
    echo -e "${GREEN}✅ Loki config exists${NC}"
else
    echo -e "${RED}❌ Loki config missing${NC}"
    exit 1
fi

if [ -f "config/promtail/config.yaml" ]; then
    echo -e "${GREEN}✅ Promtail config exists${NC}"
else
    echo -e "${RED}❌ Promtail config missing${NC}"
    exit 1
fi

if [ -f "config/grafana/provisioning/datasources/loki.yaml" ]; then
    echo -e "${GREEN}✅ Grafana datasource config exists${NC}"
else
    echo -e "${RED}❌ Grafana datasource config missing${NC}"
    exit 1
fi
echo ""

# Test log ingestion
echo "6. Testing log ingestion..."
echo "   Sending test log to Loki..."
curl -s -X POST http://localhost:3100/loki/api/v1/push \
  -H "Content-Type: application/json" \
  -d '{
    "streams": [
      {
        "stream": {
          "service": "test",
          "level": "info"
        },
        "values": [
          ["'$(date +%s%N)'", "Test log message from verification script"]
        ]
      }
    ]
  }' > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully sent test log to Loki${NC}"
else
    echo -e "${RED}❌ Failed to send test log to Loki${NC}"
    exit 1
fi
echo ""

# Query test log
echo "7. Querying test log..."
sleep 2  # Wait for log to be indexed
QUERY_RESULT=$(curl -s "http://localhost:3100/loki/api/v1/query_range?query={service=\"test\"}&limit=1")
if echo "$QUERY_RESULT" | grep -q "Test log message"; then
    echo -e "${GREEN}✅ Successfully queried test log from Loki${NC}"
else
    echo -e "${YELLOW}⚠️  Could not verify test log query${NC}"
    echo "   This may be normal if logs haven't been indexed yet"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Log Aggregation Setup Verification Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access Points:"
echo "   • Loki API: http://localhost:3100"
echo "   • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📚 Documentation:"
echo "   • Log Aggregation Guide: config/LOG_AGGREGATION.md"
echo ""
echo "🔍 Next Steps:"
echo "   1. Access Grafana at http://localhost:3000"
echo "   2. Navigate to 'Dashboards' → 'Chimera Application Logs'"
echo "   3. Start your application to see logs flowing in"
echo ""
echo "💡 Tip: Use correlation IDs to trace requests across services"
echo "   Example query: {correlation_id=\"your-id\"}"
echo ""
