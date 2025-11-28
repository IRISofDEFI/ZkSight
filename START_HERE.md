# 🚀 START HERE - Chimera Analytics

## Your System is Ready!

Everything has been configured for you. Just follow these simple steps:

## Step 1: Start Infrastructure (30 seconds)

```powershell
# Run this in PowerShell
.\scripts\start-dev.ps1
```

This starts all the databases and services you need.

## Step 2: Start the Application (30 seconds)

```powershell
# Run this in a new terminal
npm run dev:all
```

This starts both the API server and the dashboard.

## Step 3: Open Your Browser

Go to: **http://localhost:3000**

Login with:
- Email: `test@example.com`
- Password: `password123`

## That's It! 🎉

Your frontend and backend are now connected and running!

---

## What You Can Do Now

### Try the Dashboard
- Submit natural language queries
- View reports
- Create alerts
- Build custom dashboards

### Check the API
- API Health: http://localhost:3001/health
- API Docs: http://localhost:3001/api

### View Logs
- Grafana: http://localhost:3002 (admin/admin)
- Jaeger Tracing: http://localhost:16686

---

## Quick Commands

```powershell
# Start everything
npm run dev:all

# Start just the API
npm run dev:api

# Start just the dashboard
npm run dev

# Test connections
.\scripts\test-connection.ps1

# Stop infrastructure
docker-compose down

# View logs
docker-compose logs -f
```

---

## Need Help?

1. **Connection issues?** Run `.\scripts\test-connection.ps1`
2. **Port conflicts?** Check `CONNECTION_STATUS.md`
3. **Full setup guide?** See `SETUP_GUIDE.md`

---

## What's Configured

✅ All environment variables  
✅ Database connections  
✅ API server (port 3001)  
✅ Dashboard (port 3000)  
✅ WebSocket connection  
✅ CORS settings  
✅ Docker services  

Everything is ready to go!
