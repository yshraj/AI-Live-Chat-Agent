# Free Tier Deployment Guide

This guide covers deploying your AI Live Chat Agent application using **100% free tier services**.

## 🎯 Deployment Architecture

```
┌─────────────────┐
│   Frontend      │  → Vercel/Netlify (Free)
│   (React/Vite)  │
└─────────────────┘
        │
        ↓ HTTP
┌─────────────────┐
│   Backend       │  → Render/Railway (Free)
│   (FastAPI)     │
└─────────────────┘
        │
        ├─→ MongoDB Atlas (Free Tier - 512MB)
        └─→ Upstash Redis (Free Tier - 10K commands/day)
```

## 📋 Prerequisites

- GitHub account (for connecting to deployment platforms)
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- Email address for account creation

---

## 🗄️ Step 1: Set Up Databases (Free Tier)

### 1.1 MongoDB Atlas (Free Tier)

1. **Sign up**: Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. **Create a free cluster**:
   - Choose **M0 Free Tier** (512MB storage)
   - Select a cloud provider and region closest to you
   - Cluster name: `spur-chat-cluster` (or any name)
3. **Create database user**:
   - Go to **Database Access** → **Add New Database User**
   - Username: `spur-chat-user` (or any username)
   - Password: Generate a secure password (save it!)
   - Database User Privileges: **Read and write to any database**
4. **Whitelist IP addresses**:
   - Go to **Network Access** → **Add IP Address**
   - Click **Allow Access from Anywhere** (or add specific IPs)
   - This allows your backend to connect
5. **Get connection string**:
   - Go to **Clusters** → Click **Connect** → **Connect your application**
   - Copy the connection string (looks like: `mongodb+srv://<username>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority`)
   - Replace `<username>` and `<password>` with your database user credentials
   - Add database name: `mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority`
   - **Save this for Step 2!**

### 1.2 Upstash Redis (Free Tier)

1. **Sign up**: Go to [Upstash](https://upstash.com/) and create an account
2. **Create a Redis database**:
   - Click **Create Database**
   - Name: `spur-chat-redis`
   - Type: **Regional** (free tier)
   - Region: Choose closest to your backend deployment region
   - Click **Create**
3. **Get connection details**:
   - After creation, you'll see connection details
   - Copy the **UPSTASH_REDIS_REST_URL** (looks like: `https://xxx.upstash.io`)
   - Copy the **UPSTASH_REDIS_REST_TOKEN** (long token string)
   - **Save these for Step 2!**

**Note**: Upstash free tier includes:
- 10,000 commands per day
- 256MB storage
- Perfect for caching FAQ searches

---

## 🚀 Step 2: Deploy Backend (Free Tier Options)

Choose one of these platforms:

### Option A: Render.com (Recommended - Easiest)

**Free Tier Limits**:
- 750 hours/month (enough for 24/7 if you're the only user)
- Spins down after 15 minutes of inactivity (takes ~30s to wake up)
- 512MB RAM
- Free SSL certificate

**Steps**:

1. **Sign up**: Go to [Render.com](https://render.com/) and sign up with GitHub
2. **Create a new Web Service**:
   - Click **New** → **Web Service**
   - Connect your GitHub repository
   - Select the `spur-assignment` repository
3. **Configure the service**:
   - **Name**: `spur-chat-backend` (or any name)
   - **Region**: Choose closest to you
   - **Branch**: `main` (or your main branch)
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Set Environment Variables**:
   ```
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_MODEL=gemini-2.5-flash
   MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority
   MONGODB_DB_NAME=spur_chat
   UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
   UPSTASH_REDIS_REST_TOKEN=your_token_here
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```
   **Note**: For Upstash Redis, use the REST API credentials (UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN). See "Redis Configuration" section below for details.
5. **Deploy**: Click **Create Web Service**
6. **Wait for deployment** (5-10 minutes)
7. **Copy your backend URL**: `https://spur-chat-backend.onrender.com` (or your custom domain)

**Important**: Render free tier spins down after inactivity. First request after spin-down takes ~30 seconds.

### Option B: Railway.app

**Free Tier Limits**:
- $5 credit/month (enough for small apps)
- 512MB RAM
- Free SSL certificate

**Steps**:

1. **Sign up**: Go to [Railway.app](https://railway.app/) and sign up with GitHub
2. **Create a new project**:
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your repository
3. **Add a service**:
   - Click **+ New** → **GitHub Repo**
   - Select `spur-assignment`
   - Set **Root Directory** to `backend`
4. **Configure environment variables**:
   - Go to **Variables** tab
   - Add all environment variables (same as Render above)
5. **Configure start command**:
   - Go to **Settings** → **Deploy**
   - Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. **Deploy**: Railway auto-deploys on push

### Option C: Fly.io

**Free Tier Limits**:
- 3 shared-cpu VMs
- 3GB persistent volumes
- 160GB outbound data transfer/month

**Steps**:

1. **Install Fly CLI**: Follow [Fly.io installation guide](https://fly.io/docs/getting-started/installing-flyctl/)
2. **Sign up**: Run `flyctl auth signup`
3. **Create app**:
   ```bash
   cd backend
   flyctl launch
   ```
   - App name: `spur-chat-backend` (or any unique name)
   - Region: Choose closest
   - Don't deploy yet (we'll configure first)
4. **Set secrets**:
   ```bash
   flyctl secrets set GOOGLE_API_KEY=your_key_here
   flyctl secrets set GOOGLE_MODEL=gemini-2.5-flash
   flyctl secrets set MONGODB_URL=your_mongodb_url
   flyctl secrets set MONGODB_DB_NAME=spur_chat
   flyctl secrets set REDIS_URL=your_redis_url
   ```
5. **Create `fly.toml`** in `backend/` directory:
   ```toml
   app = "spur-chat-backend"
   primary_region = "iad"

   [build]
     dockerfile = "Dockerfile"

   [[services]]
     internal_port = 8000
     protocol = "tcp"

     [[services.ports]]
       handlers = ["http"]
       port = 80

     [[services.ports]]
       handlers = ["tls", "http"]
       port = 443

     [[services.http_checks]]
       interval = "10s"
       timeout = "2s"
       grace_period = "5s"
       method = "GET"
       path = "/health"
   ```
6. **Deploy**:
   ```bash
   flyctl deploy
   ```

---

## 🎨 Step 3: Deploy Frontend (Free Tier)

### Option A: Vercel (Recommended - Best Performance)

**Free Tier Limits**:
- Unlimited projects
- 100GB bandwidth/month
- Automatic SSL
- Global CDN

**Steps**:

1. **Sign up**: Go to [Vercel.com](https://vercel.com/) and sign up with GitHub
2. **Import project**:
   - Click **Add New Project**
   - Import your GitHub repository
   - Select `spur-assignment`
3. **Configure project**:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
4. **Set Environment Variables**:
   - Go to **Settings** → **Environment Variables**
   - Add: `VITE_API_URL` = `https://your-backend-url.onrender.com` (or Railway/Fly.io URL)
5. **Deploy**: Click **Deploy**
6. **Copy your frontend URL**: `https://spur-assignment.vercel.app` (or custom domain)

### Option B: Netlify

**Free Tier Limits**:
- 100GB bandwidth/month
- 300 build minutes/month
- Automatic SSL

**Steps**:

1. **Sign up**: Go to [Netlify.com](https://www.netlify.com/) and sign up with GitHub
2. **Add new site**:
   - Click **Add new site** → **Import an existing project**
   - Connect to GitHub and select your repository
3. **Configure build settings**:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/dist`
4. **Set environment variables**:
   - Go to **Site settings** → **Environment variables**
   - Add: `VITE_API_URL` = `https://your-backend-url.onrender.com`
5. **Deploy**: Click **Deploy site**

---

## ⚙️ Step 4: Configure Redis for Upstash

Upstash uses REST API instead of traditional Redis protocol. You'll need to update your backend code to use Upstash REST API.

### Update Backend Code

Create a new file `backend/app/db/upstash_redis.py`:

```python
"""Upstash Redis client using REST API."""
import os
import httpx
from typing import Optional
import json


class UpstashRedisClient:
    """Upstash Redis client using REST API."""
    
    def __init__(self):
        self.rest_url = os.getenv("UPSTASH_REDIS_REST_URL")
        self.rest_token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self.client = httpx.AsyncClient(
            base_url=self.rest_url,
            headers={"Authorization": f"Bearer {self.rest_token}"},
            timeout=10.0
        )
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            response = await self.client.post("/", json=["GET", key])
            if response.status_code == 200:
                result = response.json()
                return result.get("result") if result.get("result") else None
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration."""
        try:
            if ex:
                response = await self.client.post("/", json=["SET", key, value, "EX", str(ex)])
            else:
                response = await self.client.post("/", json=["SET", key, value])
            return response.status_code == 200
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        try:
            response = await self.client.post("/", json=["DEL", key])
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Singleton instance
upstash_client = UpstashRedisClient()
```

Then update `backend/app/db/redis_client.py` to use Upstash when environment variables are set:

```python
"""Redis client with fallback to Upstash."""
import os
from typing import Optional

# Try to import redis, fallback to Upstash if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Check if Upstash is configured
UPSTASH_URL = os.getenv("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN")
USE_UPSTASH = bool(UPSTASH_URL and UPSTASH_TOKEN)

if USE_UPSTASH:
    from .upstash_redis import upstash_client as redis_client
else:
    if REDIS_AVAILABLE:
        redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True
        )
    else:
        redis_client = None
```

**Add httpx to requirements.txt**:
```bash
httpx==0.25.2  # Already included for testing, but ensure it's there
```

**Set environment variables** on your backend platform:
```
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_token_here
```

---

## 🌱 Step 5: Seed FAQs in Production

After deploying, you need to seed FAQs in your MongoDB Atlas database.

### Option A: Run Seed Script Locally (Pointing to Atlas)

1. **Update your local `.env`**:
   ```bash
   MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority
   MONGODB_DB_NAME=spur_chat
   ```

2. **Run seed script**:
   ```bash
   cd backend
   python scripts/seed_faqs.py
   ```

### Option B: Create a One-Time API Endpoint

Add this to `backend/app/api/routes/chat.py` temporarily:

```python
@router.post("/admin/seed-faqs")
async def seed_faqs_endpoint():
    """One-time endpoint to seed FAQs."""
    from app.services.faq_service import FAQService
    from scripts.seed_faqs import seed_faqs
    
    try:
        seed_faqs()
        return {"status": "success", "message": "FAQs seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Then call it once: `POST https://your-backend-url.onrender.com/admin/seed-faqs`

**Remember to remove this endpoint after seeding!**

---

## ✅ Step 6: Verify Deployment

1. **Check backend health**:
   - Visit: `https://your-backend-url.onrender.com/health`
   - Should return: `{"status": "healthy", "message": "Service is running"}`

2. **Check frontend**:
   - Visit your Vercel/Netlify URL
   - Open browser console (F12)
   - Verify no CORS errors
   - Try sending a chat message

3. **Test chat functionality**:
   - Send a message in the chat widget
   - Verify AI response comes back
   - Check MongoDB Atlas to see if conversations are being saved

---

## 🔧 Troubleshooting

### Backend Issues

**Problem**: Backend returns 503 or times out
- **Solution**: Render free tier spins down after 15 min inactivity. First request takes ~30s to wake up.

**Problem**: MongoDB connection fails
- **Solution**: 
  - Verify IP whitelist includes `0.0.0.0/0` (all IPs)
  - Check connection string format
  - Verify database user password is correct

**Problem**: Redis/Upstash errors
- **Solution**: 
  - Verify `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are set
  - Check Upstash dashboard for quota limits
  - Verify httpx is installed: `pip install httpx`

### Frontend Issues

**Problem**: Frontend can't connect to backend
- **Solution**: 
  - Verify `VITE_API_URL` is set correctly
  - Check CORS settings in backend (should allow your frontend domain)
  - Check browser console for errors

**Problem**: CORS errors
- **Solution**: Update `backend/app/main.py` to include your frontend domain:
  ```python
  from fastapi.middleware.cors import CORSMiddleware
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "https://your-frontend.vercel.app",
          "https://your-frontend.netlify.app",
          "http://localhost:3000",  # For local development
      ],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### Database Issues

**Problem**: FAQs not found
- **Solution**: Run seed script (Step 5)

**Problem**: MongoDB Atlas free tier limits
- **Solution**: 
  - Free tier: 512MB storage
  - Monitor usage in Atlas dashboard
  - Consider archiving old conversations if needed

---

## 💰 Cost Summary (Free Tier)

| Service | Free Tier Limits | Cost |
|---------|-----------------|------|
| **Render.com** | 750 hours/month | $0 |
| **Vercel** | Unlimited projects, 100GB bandwidth | $0 |
| **MongoDB Atlas** | 512MB storage | $0 |
| **Upstash Redis** | 10K commands/day, 256MB | $0 |
| **Google Gemini API** | Free tier available | $0* |

*Google Gemini has a free tier, but check current limits at [Google AI Studio](https://makersuite.google.com/app/apikey)

**Total Monthly Cost: $0** 🎉

---

## 🚀 Quick Deploy Checklist

- [ ] MongoDB Atlas cluster created and connection string copied
- [ ] Upstash Redis database created and tokens copied
- [ ] Backend deployed (Render/Railway/Fly.io)
- [ ] Environment variables set on backend platform
- [ ] Frontend deployed (Vercel/Netlify)
- [ ] `VITE_API_URL` set to backend URL
- [ ] FAQs seeded in MongoDB Atlas
- [ ] Health check endpoint working
- [ ] Chat functionality tested
- [ ] CORS configured correctly

---

## 📚 Additional Resources

- [Render.com Documentation](https://render.com/docs)
- [Vercel Documentation](https://vercel.com/docs)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Upstash Documentation](https://docs.upstash.com/)
- [Google Gemini API Documentation](https://ai.google.dev/docs)

---

## 🎉 You're Done!

Your application should now be live and accessible from anywhere. Share your frontend URL with others to test!

**Note**: Free tier services have limitations. For production use with high traffic, consider upgrading to paid tiers or using alternative services.

