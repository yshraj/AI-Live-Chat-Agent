# Quick Start Guide

## Prerequisites Check

```bash
# Check Python version (need 3.9+)
python --version

# Check Node.js version (need 18+)
node --version

# Check Docker
docker --version
docker-compose --version
```

## Quick Setup (5 minutes)

### 1. Start Databases

```bash
docker-compose -f scripts/docker-compose.yml up -d
```

Wait ~10 seconds for services to start.

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
venv\Scripts\activate
# Windows (CMD):
venv\Scripts\activate.bat
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
# Windows (PowerShell):
Copy-Item .env.example .env
# Mac/Linux:
cp .env.example .env

# Edit .env and add your Google Gemini API key:
# Get your API key from: https://makersuite.google.com/app/apikey
# GOOGLE_API_KEY=your_google_api_key_here
# Optional: GOOGLE_MODEL=gemini-2.5-flash (defaults to gemini-2.5-flash)
```

**Note**: 
- If you get `ModuleNotFoundError: No module named 'bson'`, do NOT install `bson` separately. It comes with `pymongo`. Just run `pip install -r requirements.txt` to install all dependencies.
- If you get `ImportError: cannot import name 'cached_download' from 'huggingface_hub'`, this is a version compatibility issue. Run `pip install -r requirements.txt --upgrade` to install compatible versions.

### 3. Seed FAQs

```bash
python scripts/seed_faqs.py
```

### 4. Start Backend

```bash
uvicorn app.main:app --reload
```

Backend runs on `http://localhost:8000`

### 5. Frontend Setup (New Terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000` (or port shown)

## Test It!

1. Open `http://localhost:3000` in your browser
2. Type: "What is your return policy?"
3. You should get an AI response!

## Troubleshooting

**MongoDB not connecting?**
```bash
docker ps | grep mongodb
docker-compose -f scripts/docker-compose.yml restart mongodb
```

**Redis not connecting?**
```bash
docker ps | grep redis
docker-compose -f scripts/docker-compose.yml restart redis
```

**Backend errors?**
- Check `.env` file has `GOOGLE_API_KEY` set
- Check MongoDB and Redis are running
- Check backend logs for errors
- If you see `ModuleNotFoundError`, ensure virtual environment is activated and run `pip install -r requirements.txt`

**Frontend not connecting?**
- Check backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend `.env`

## Next Steps

- Read the full [README.md](README.md) for detailed architecture
- Check API docs at `http://localhost:8000/docs`
- Run tests: `cd backend && pytest`

