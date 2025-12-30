# Quick Deploy Reference

This is a quick reference guide. For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🎯 Free Tier Stack

| Component | Service | Free Tier |
|-----------|---------|-----------|
| **Frontend** | Vercel | Unlimited projects, 100GB bandwidth |
| **Backend** | Render.com | 750 hours/month |
| **MongoDB** | MongoDB Atlas | 512MB storage |
| **Redis** | Upstash | 10K commands/day |

## ⚡ 5-Minute Deploy

### 1. Databases (5 min)

**MongoDB Atlas:**
1. Sign up at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas/register)
2. Create M0 free cluster
3. Create database user
4. Whitelist IP: `0.0.0.0/0`
5. Copy connection string

**Upstash Redis:**
1. Sign up at [upstash.com](https://upstash.com/)
2. Create Regional database
3. Copy REST URL and token

### 2. Backend (5 min)

**Render.com:**
1. Sign up at [render.com](https://render.com/)
2. New → Web Service
3. Connect GitHub repo
4. Settings:
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   ```
   GOOGLE_API_KEY=your_key
   MONGODB_URL=your_atlas_url
   UPSTASH_REDIS_REST_URL=your_upstash_url
   UPSTASH_REDIS_REST_TOKEN=your_token
   ```
6. Deploy!

### 3. Frontend (2 min)

**Vercel:**
1. Sign up at [vercel.com](https://vercel.com/)
2. Import GitHub repo
3. Settings:
   - Root Directory: `frontend`
   - Build: `npm run build`
   - Output: `dist`
4. Environment Variable:
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```
5. Deploy!

### 4. Seed FAQs (1 min)

Run locally pointing to Atlas:
```bash
cd backend
# Update .env with MongoDB Atlas URL
python scripts/seed_faqs.py
```

Or create temporary endpoint (see DEPLOYMENT.md Step 5).

## ✅ Done!

Your app is live at: `https://your-app.vercel.app`

## 🔧 Troubleshooting

**Backend won't start?**
- Check environment variables are set
- Check MongoDB connection string format
- Check Upstash tokens are correct

**Frontend can't connect?**
- Check `VITE_API_URL` is set
- Check CORS settings in backend
- Add frontend URL to `CORS_ORIGINS` env var

**No FAQs?**
- Run seed script (Step 4 above)

**CORS errors?**
- Add frontend URL to backend `CORS_ORIGINS` env var
- Format: `https://your-app.vercel.app,https://your-app.netlify.app`

## 📚 Full Guide

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Detailed step-by-step instructions
- Screenshots and examples
- Advanced configuration
- Troubleshooting guide

