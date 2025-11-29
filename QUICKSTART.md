# 🚀 Archon Quick Start Guide

## First Time Setup

Run the automated setup script:
```bash
./setup.sh
```

This will:
- ✅ Check/Install Redis
- ✅ Create .env from template
- ✅ Setup Python virtual environment
- ✅ Install all dependencies
- ✅ (Optional) Seed test data

**⚠️ Important:** You'll need to add your Supabase credentials to `.env`:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`

## Start Archon

After setup, start both backend and frontend:
```bash
./start.sh
```

This starts:
- Backend: http://localhost:8181
- Frontend: http://localhost:5173

## Stop Archon

```bash
./stop.sh
```

## Manual Start (Alternative)

### Terminal 1: Backend
```bash
cd python
source .venv/bin/activate
python -m uvicorn src.server.main:app --host 0.0.0.0 --port 8181 --reload
```

### Terminal 2: Frontend
```bash
cd archon-ui-main
npm run dev
```

## Troubleshooting

### Redis not starting?
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# Verify
redis-cli ping  # Should return "PONG"
```

### Port already in use?
```bash
# Kill process on port 8181
lsof -ti:8181 | xargs kill -9

# Or use the stop script
./stop.sh
```

### Backend fails to start?
Check `backend.log` for errors:
```bash
tail -f backend.log
```

Most common issues:
1. **Missing .env variables** - Check SUPABASE_URL and SUPABASE_SERVICE_KEY
2. **Redis not running** - Run `redis-cli ping`
3. **Port conflict** - Run `./stop.sh` first

### Frontend fails to start?
Check `frontend.log`:
```bash
tail -f frontend.log
```

## Logs

- Backend logs: `backend.log`
- Frontend logs: `frontend.log`

## First Steps After Setup

1. **Open Frontend:** http://localhost:5173
2. **Go to Memory Inspector:** http://localhost:5173/memory
3. **Check API Docs:** http://localhost:8181/docs

## Need Help?

- Check: `DOCKER_TROUBLESHOOTING.md`
- Check: `production_readiness.md` (in .gemini/antigravity/brain/)
