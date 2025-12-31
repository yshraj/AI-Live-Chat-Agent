# AI Live Chat Agent

A full-stack AI-powered live chat support agent built with FastAPI (backend) and React (frontend), featuring MongoDB Atlas for persistence, Upstash Redis for caching, Google Gemini LLM integration, and vector embeddings for FAQ retrieval.

## 🎯 Project Overview

This is a production-ready AI chat agent that demonstrates:
- ✅ **End-to-end chat functionality** with real LLM integration
- ✅ **Conversation persistence** with automatic history restoration
- ✅ **Robust error handling** for network issues, API failures, and edge cases
- ✅ **Clean architecture** with clear separation of concerns
- ✅ **Extensible design** ready for multi-channel support (WhatsApp, Instagram, etc.)
- ✅ **Cost optimization** with conditional RAG and smart caching
- ✅ **Modern UI/UX** with markdown support and responsive design

## Tech Stack

- **Backend**: Python FastAPI (async)
- **Frontend**: React + TypeScript (Vite)
- **Database**: MongoDB (via Docker locally, or MongoDB Atlas for production)
- **Cache**: Redis (via Docker locally, or Upstash Redis for production)
- **LLM**: Google Gemini API (gemini-2.5-flash)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) for FAQ semantic search
- **Testing**: pytest + pytest-asyncio

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── services/        # Business logic (LLM, FAQ, Chat)
│   │   ├── models/          # MongoDB models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── db/              # Database connections
│   │   ├── core/            # Config, exceptions
│   │   └── utils/           # Utilities
│   ├── tests/               # Test files
│   ├── scripts/             # Seed scripts
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   ├── services/        # API client
│   │   └── types/           # TypeScript types
│   └── package.json
├── scripts/
│   └── docker-compose.yml   # MongoDB + Redis
└── README.md
```

## How to Run Locally

### Prerequisites

- **Python 3.9+** (check with `python --version`)
- **Node.js 18+** (check with `node --version`)
- **Docker and Docker Compose** (check with `docker --version`)
- **Google Gemini API key** ([Get one here](https://makersuite.google.com/app/apikey))

### Quick Start (5 minutes)

For a quick start guide, see [QUICKSTART.md](QUICKSTART.md)

### Step-by-Step Setup

#### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
venv\Scripts\activate
# On Windows (CMD):
venv\Scripts\activate.bat
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Note: If you encounter "ModuleNotFoundError: No module named 'bson'",
# do NOT install bson separately. The bson module comes with pymongo.
# Simply ensure pymongo is installed: pip install pymongo==4.6.0

# Copy and configure environment variables
# On Windows (PowerShell):
Copy-Item .env.example .env
# On Mac/Linux:
cp .env.example .env

# Edit .env and add your GOOGLE_API_KEY
```

#### 2. Database Setup & Migrations

**Option A: Local Development (Docker)**

Start MongoDB and Redis using Docker Compose:
```bash
# Start services using Docker Compose
docker-compose -f scripts/docker-compose.yml up -d

# Wait for services to be ready (about 10 seconds)
# Verify MongoDB is running:
docker ps | grep mongodb
# On Windows PowerShell:
docker ps | Select-String mongodb

# Verify Redis is running:
docker ps | grep redis
# On Windows PowerShell:
docker ps | Select-String redis
```

**Option B: Production/Cloud Setup (MongoDB Atlas + Upstash Redis)**

For production deployment, you can use cloud services instead of Docker:

1. **MongoDB Atlas** (Free tier - 512MB):
   - Sign up at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
   - Create a free M0 cluster
   - Get your connection string: `mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority`
   - Set `MONGODB_URL` in your `.env` file

2. **Upstash Redis** (Free tier - 10K commands/day):
   - Sign up at [Upstash](https://upstash.com/)
   - Create a free Regional Redis database
   - Get your REST API credentials or connection string
   - Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` in your `.env` file
   - Or use `UPSTASH_REDIS_URL` with connection string format

**Note**: MongoDB automatically creates indexes on startup (no manual migrations needed). Indexes are created in `app/db/mongodb.py`:
- `conversations.session_id` (unique)
- `messages.conversation_id`
- `messages.created_at`
- Composite index: `(conversation_id, created_at)`

For detailed cloud setup instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

#### 3. Seed FAQs (Database Seeding)

**Populate FAQs:**
```bash
cd backend
# Ensure virtual environment is activated
python scripts/seed_faqs.py
```

This script will:
- Generate vector embeddings for each FAQ using `all-MiniLM-L6-v2`
- Store FAQs in MongoDB `faqs` collection
- Clear existing FAQs and insert new ones

**Sample FAQs included:**
- Shipping policy and timelines
- Return and refund policies
- Support hours
- Order tracking information

**To verify seeding worked:**
```bash
# Connect to MongoDB
docker exec -it spur_mongodb mongosh spur_chat

# Check FAQs
db.faqs.find().pretty()
```

#### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional, defaults to http://localhost:8000)
echo "VITE_API_URL=http://localhost:8000" > .env
```

#### 5. Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Open your browser:**
- Frontend: `http://localhost:3000` (or the port shown by Vite)
- Backend API docs: `http://localhost:8000/docs`

## Environment Variables Configuration

### Backend Environment Variables (`backend/.env`)

**Required:**
```bash
# Google Gemini API (REQUIRED)
# Get your API key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here
```

**Optional (with defaults):**
```bash
# Google Gemini Model Configuration
GOOGLE_MODEL=gemini-2.5-flash   # Model name (e.g., gemini-2.5-flash, gemini-3-flash)

# MongoDB Configuration
# For local development (Docker):
MONGODB_URL=mongodb://localhost:27017
# For production (MongoDB Atlas):
# MONGODB_URL=mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority
MONGODB_DB_NAME=spur_chat

# Redis Configuration
# For local development (Docker):
REDIS_URL=redis://localhost:6379
# For production (Upstash Redis):
# Option 1: Using REST API (recommended for serverless)
# UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
# UPSTASH_REDIS_REST_TOKEN=your_token_here
# Option 2: Using connection string
# UPSTASH_REDIS_URL=rediss://default:password@xxx.upstash.io:6379

# Application Settings
MAX_MESSAGE_LENGTH=2000          # Max characters per message
LLM_MAX_TOKENS=500              # Max tokens in LLM response
LLM_TEMPERATURE=0.7             # LLM creativity (0.0-1.0)
MESSAGE_HISTORY_LIMIT=10        # Number of messages in context
```

**Setup Steps:**
1. Copy `.env.example` to `.env`:
   ```bash
   # Windows (PowerShell):
   Copy-Item .env.example .env
   # Mac/Linux:
   cp .env.example .env
   ```

2. Edit `.env` and add your Google Gemini API key:
   ```bash
   GOOGLE_API_KEY=your_google_api_key_here
   GOOGLE_MODEL=gemini-2.5-flash  # Optional: defaults to gemini-2.5-flash
   ```

3. **Important Notes**:
   - Get your API key from: https://makersuite.google.com/app/apikey
   - Available models: `gemini-2.5-flash`, `gemini-3-flash`, `gemini-robotics-er-1.5-preview`, etc.
   - Never commit `.env` file to git (already in `.gitignore`)

### Frontend Environment Variables (`frontend/.env`)

**Optional (defaults to `http://localhost:8000`):**
```bash
VITE_API_URL=http://localhost:8000
```

**Setup:**
```bash
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env
```

**Note**: For production, update `VITE_API_URL` to your production backend URL.

### Choosing Between Docker and Cloud Services

**Use Docker (Local Development):**
- ✅ Quick setup for local development
- ✅ No external dependencies
- ✅ Free and unlimited usage
- ✅ Good for testing and development

**Use MongoDB Atlas + Upstash Redis (Production/Cloud):**
- ✅ No need to manage Docker containers
- ✅ Better for production deployments
- ✅ Free tiers available:
  - MongoDB Atlas: 512MB storage (M0 free tier)
  - Upstash Redis: 10,000 commands/day, 256MB storage
- ✅ Automatic backups and scaling options
- ✅ Better for serverless deployments (Render, Vercel, etc.)

**The application automatically detects and uses the appropriate service based on your environment variables:**
- If `MONGODB_URL` starts with `mongodb+srv://`, it uses MongoDB Atlas
- If `UPSTASH_REDIS_REST_URL` or `UPSTASH_REDIS_URL` is set, it uses Upstash Redis
- Otherwise, it falls back to local Docker services

For detailed cloud setup instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Testing

### Backend Tests

```bash
cd backend
pytest

# Run with coverage
pytest --cov=app tests/
```

### Test Structure

- `test_llm_service.py` - Tests for LLM integration with mocked Google Gemini API
- `test_faq_service.py` - Tests for FAQ retrieval and embedding matching
- `test_chat.py` - Tests for chat service logic
- `test_api.py` - Integration tests for API endpoints

## Architecture Overview

See the detailed architecture section below for comprehensive information about backend structure, design decisions, and extensibility.

## FAQ System

### Embedding Model

- **Model**: `all-MiniLM-L6-v2` (sentence-transformers)
- **Vector Size**: 384 dimensions
- **Storage**: Embeddings stored in MongoDB `faqs` collection

### Semantic Search

1. User query → Generate embedding
2. Calculate cosine similarity with all FAQ embeddings
3. Return top 3 most similar FAQs
4. Include FAQs in LLM context

### Caching

- FAQ search results cached in Redis (TTL: 1 hour)
- Cache key: `faq_search:{query_hash}`
- Graceful degradation if Redis unavailable

## API Endpoints

### `POST /chat/message`

Send a message and receive AI response.

**Request:**
```json
{
  "message": "What is your return policy?",
  "sessionId": "optional-session-id"
}
```

**Response:**
```json
{
  "reply": "We offer a 30-day return policy...",
  "sessionId": "uuid-session-id"
}
```

**Error Responses:**
- `400`: Validation error (empty message, too long)
- `503`: LLM service unavailable
- `500`: Server error

### `GET /chat/history/{session_id}`

Get conversation history for a session.

**Response:**
```json
{
  "messages": [
    {
      "sender": "user",
      "content": "Hello",
      "created_at": "2024-01-01T00:00:00"
    },
    {
      "sender": "ai",
      "content": "Hi there!",
      "created_at": "2024-01-01T00:00:01"
    }
  ]
}
```

### `GET /health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Service is running"
}
```

## Database Schema

### Collections

**conversations**
```javascript
{
  _id: ObjectId,
  session_id: String (UUID, unique),
  created_at: DateTime,
  updated_at: DateTime
}
```

**messages**
```javascript
{
  _id: ObjectId,
  conversation_id: ObjectId,
  sender: "user" | "ai",
  content: String,
  created_at: DateTime
}
```

**faqs**
```javascript
{
  _id: ObjectId,
  category: String,
  question: String,
  answer: String,
  embedding: [Float],  // 384-dimensional vector
  created_at: DateTime
}
```

### Indexes

- `conversations.session_id` (unique)
- `messages.conversation_id`
- `messages.created_at`
- Composite: `(conversation_id, created_at)`

## Deployment

### 🚀 Free Tier Deployment Guide

**For detailed step-by-step instructions on deploying to free tier services, see [DEPLOYMENT.md](DEPLOYMENT.md)**

The deployment guide covers:
- ✅ **MongoDB Atlas** (Free tier - 512MB)
- ✅ **Upstash Redis** (Free tier - 10K commands/day)
- ✅ **Render.com** (Free tier - 750 hours/month)
- ✅ **Vercel** (Free tier - Unlimited projects)
- ✅ **Complete setup instructions** with screenshots and troubleshooting

### Quick Deployment Summary

**Backend Deployment Options:**
- **Render.com**: Use `render.yaml` config file (recommended)
- **Railway.app**: Use `railway.json` config file
- **Fly.io**: Use Dockerfile with `flyctl deploy`

**Frontend Deployment Options:**
- **Vercel**: Use `vercel.json` config file (recommended)
- **Netlify**: Drag and drop `frontend/dist` folder

**Database Setup:**
- **MongoDB**: Use MongoDB Atlas free tier (512MB)
  - Connection string format: `mongodb+srv://<username>:<password>@cluster.mongodb.net/spur_chat?retryWrites=true&w=majority`
  - Set `MONGODB_URL` environment variable
- **Redis**: Use Upstash free tier (10K commands/day)
  - Option 1: REST API (recommended for serverless) - Set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
  - Option 2: Connection string - Set `UPSTASH_REDIS_URL` (format: `rediss://default:password@xxx.upstash.io:6379`)

### Environment Setup for Production

1. Set environment variables on hosting platform (see DEPLOYMENT.md)
2. Update `VITE_API_URL` to production backend URL
3. Configure MongoDB Atlas and Upstash Redis
4. Run seed script to populate FAQs (see DEPLOYMENT.md Step 5)

### Docker Deployment (Alternative)

The backend includes a `Dockerfile` for containerization:

```bash
# Build image
docker build -t spur-chat-backend ./backend

# Run container
docker run -p 8000:8000 --env-file backend/.env spur-chat-backend
```

## Architecture Overview

### Backend Structure

The backend follows a **layered architecture** with clear separation of concerns:

#### 1. **API Layer** (`app/api/routes/`)
- **Purpose**: HTTP request handling and validation
- **Files**: `chat.py`, `health.py`
- **Responsibilities**:
  - Route definitions and HTTP methods
  - Request/response validation using Pydantic schemas
  - Error handling and status codes
  - Input sanitization (message length, empty checks)

#### 2. **Service Layer** (`app/services/`)
- **Purpose**: Business logic and orchestration
- **Files**:
  - `chat_service.py`: Orchestrates message processing, handles greetings, manages conversation flow
  - `llm_service.py`: LLM API integration, prompt management, retry logic
  - `faq_service.py`: Semantic search, FAQ retrieval, caching
  - `embedding_service.py`: Vector embedding generation
- **Design Decision**: Services are stateless and testable. Each service has a single responsibility.

#### 3. **Data Layer** (`app/models/`)
- **Purpose**: Database abstraction
- **Files**: `conversation.py`, `message.py`, `faq.py`
- **Pattern**: Active Record pattern - models encapsulate data and database operations
- **Design Decision**: Models handle their own persistence, making the codebase more intuitive

#### 4. **Core Layer** (`app/core/`)
- **Purpose**: Configuration and shared utilities
- **Files**: `config.py`, `exceptions.py`
- **Design Decision**: Centralized configuration via environment variables prevents hard-coded values

### Frontend Structure

The frontend follows **component-based architecture**:

- **Components** (`components/`): Presentational React components
  - `ChatWidget`: Container component managing overall chat state
  - `MessageList`: Displays messages with auto-scroll
  - `Message`: Individual message bubble with markdown support
  - `MessageInput`: Input field with auto-resize
  - `TypingIndicator`: Loading animation

- **Hooks** (`hooks/`): Custom React hooks for state management
  - `useChat`: Manages chat state, API calls, session persistence, history loading

- **Services** (`services/`): API client abstraction
  - `api.ts`: Centralized API calls with error handling

- **Utils** (`utils/`): Helper functions
  - `storage.ts`: localStorage abstraction for session management

### Interesting Design Decisions

1. **Atomic Message Saving**: Both user and AI messages are saved together via `_save_message_pair()` to ensure data consistency. If one fails, both fail together.

2. **Conditional RAG**: Greetings and simple queries skip RAG/LLM calls to reduce costs. This is a pragmatic optimization that maintains UX while saving API costs.

3. **Conversation History Tracking**: Conversation model tracks `message_count` and `last_message_at` for quick stats without querying all messages.

4. **Semantic Search with Caching**: FAQ embeddings are cached in Redis to avoid recomputation. Falls back gracefully if Redis is unavailable.

5. **Session Persistence**: Session IDs stored in localStorage enable conversation history restoration on page reload.

6. **Error Recovery**: Multiple layers of error handling - service level, API level, and UI level - ensure graceful degradation.

7. **Markdown Support**: AI messages render markdown for better formatting (lists, bold, code blocks) while user messages remain plain text.

## LLM Integration

### Provider: Google Gemini

**Why Google Gemini?**
- Fast response times with `gemini-2.5-flash` or `gemini-3-flash`
- Cost-effective for high-volume support
- Good API stability and rate limits
- Easy integration with Google Cloud services
- Free tier available for testing

### Prompt Engineering

**System Prompt Structure:**
```
1. Role Definition: "You are an AI customer support agent..."
2. Purpose: What the agent should do
3. Capabilities: What it CAN do
4. Limitations: What it CANNOT do (out-of-scope handling)
5. Brand Voice: Communication style guidelines
6. Important Guidelines: Edge case handling
```

**Context Injection:**
- **Conversation History**: Last 10 messages included for context
- **FAQ Context**: Top 3 most relevant FAQs injected via semantic search
- **System Instructions**: Brand voice and guidelines included in every request

**Prompt Flow:**
1. User message arrives
2. Check if greeting → skip RAG/LLM (cost optimization)
3. If not greeting → retrieve relevant FAQs via semantic search
4. Build system prompt with FAQ context
5. Include conversation history
6. Send to Google Gemini API
7. Return formatted response

### Trade-offs

**Current Approach:**
- ✅ **Pros**: Simple, fast, cost-effective with conditional RAG
- ✅ **Pros**: Good error handling with retry logic
- ✅ **Pros**: Clear separation of concerns
- ⚠️ **Cons**: System prompt included in every message (token overhead)
- ⚠️ **Cons**: No streaming responses (users wait for full response)
- ⚠️ **Cons**: Synchronous MongoDB operations (could be async)

**Alternative Approaches Considered:**
- **Streaming Responses**: Would improve UX but adds complexity
- **MongoDB Atlas Vector Search**: Better for production scale but requires cloud setup
- **Pre-computed Embeddings**: Faster but requires migration script
- **Motor (async MongoDB)**: Better performance but adds complexity

### Configuration

- **Max Tokens**: 500 (configurable via `LLM_MAX_TOKENS`)
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Retry Logic**: 3 attempts with exponential backoff (1s, 2s, 4s)
- **History Limit**: Last 10 messages included in context

## Trade-offs & "If I Had More Time..."

### Current Trade-offs

1. **Synchronous MongoDB**: Using PyMongo (sync) instead of Motor (async) for simplicity. Works fine for this scale but would benefit from async for production.

2. **In-Memory Embedding Generation**: Embeddings generated on-the-fly. For production, pre-compute and cache embeddings.

3. **Simple Vector Search**: Cosine similarity works well for small FAQ sets. For scale, MongoDB Atlas Vector Search would be better.

4. **No Streaming**: LLM responses wait for completion. Streaming would improve perceived performance.

5. **Session-based Auth**: Simple UUID sessions. For production, add proper authentication.

6. **No Rate Limiting**: No per-user rate limits. Would need for production.

### If I Had More Time...

**Immediate Improvements:**
1. **Streaming Responses**: Implement Server-Sent Events (SSE) or WebSockets for real-time streaming
2. **Better Error Messages**: More specific error handling with user-friendly messages
3. **Message Pagination**: For very long conversations
4. **Typing Indicators**: More sophisticated typing indicators with estimated time

**Architecture Enhancements:**
1. **Async MongoDB**: Migrate to Motor for better async performance
2. **Message Queue**: Add Redis/RabbitMQ for handling high-volume requests
3. **Caching Layer**: Cache LLM responses for common queries
4. **Analytics**: Track conversation metrics, user satisfaction, common questions

**Feature Additions:**
1. **Multi-channel Support**: Easy to add WhatsApp, Instagram, etc. via adapter pattern
   - Create `ChannelAdapter` interface
   - Implement `WebAdapter`, `WhatsAppAdapter`, etc.
   - Route messages through adapters
2. **File Attachments**: Support images, documents in chat
3. **Voice Messages**: Transcribe and respond to voice messages
4. **Multi-language**: Internationalization support
5. **Admin Dashboard**: View conversations, analytics, manage FAQs

**Production Readiness:**
1. **Authentication**: User authentication and authorization
2. **Rate Limiting**: Per-user and per-IP rate limits
3. **Monitoring**: APM, logging, error tracking (Sentry, DataDog)
4. **Testing**: More comprehensive test coverage, E2E tests
5. **CI/CD**: Automated testing and deployment pipelines
6. **Documentation**: API documentation, deployment guides

**Scalability:**
1. **Horizontal Scaling**: Stateless backend enables easy scaling
2. **Database Sharding**: For very large conversation volumes
3. **CDN**: For static frontend assets
4. **Load Balancing**: Multiple backend instances

### Extensibility Design

The architecture is designed for easy extension:

**Adding New Channels:**
```python
# Easy to add new channels via adapter pattern
class ChannelAdapter:
    async def send_message(self, message: str) -> str
    async def receive_message(self) -> Message

# Implementations:
class WhatsAppAdapter(ChannelAdapter): ...
class InstagramAdapter(ChannelAdapter): ...
```

**Adding New LLM Providers:**
```python
# LLM service is abstracted
class LLMProvider:
    async def generate_reply(self, ...) -> str

# Easy to swap providers
class OpenAIProvider(LLMProvider): ...
class ClaudeProvider(LLMProvider): ...
```

**Adding New Tools:**
- Tools can be added as services
- Integrate via service layer
- No changes needed to API or models

## Troubleshooting

### Python Dependencies Issues

**Error: `ModuleNotFoundError: No module named 'bson'`**
- **Solution**: Do NOT install `bson` as a separate package. The `bson` module comes with `pymongo`.
- Run: `pip install pymongo==4.6.0` (or `pip install -r requirements.txt` to install all dependencies)

**Error: `ModuleNotFoundError: No module named 'pymongo'`**
- **Solution**: Install dependencies from requirements.txt:
  ```bash
  cd backend
  pip install -r requirements.txt
  ```

**Error: `ImportError: cannot import name 'cached_download' from 'huggingface_hub'`**
- **Solution**: This occurs when `sentence-transformers==2.2.2` is used with newer `huggingface-hub`. The requirements.txt has been updated to use compatible versions (`sentence-transformers>=2.3.0`). Reinstall dependencies:
  ```bash
  cd backend
  pip install -r requirements.txt --upgrade
  ```

**Error: `pip install -r backend/r` (incomplete path)**
- **Solution**: Use the full path: `pip install -r backend/requirements.txt`
- Or navigate to backend directory first: `cd backend && pip install -r requirements.txt`

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
docker ps | grep mongodb
# On Windows PowerShell:
docker ps | Select-String mongodb

# Check MongoDB logs
docker logs spur_mongodb

# Restart MongoDB
docker-compose -f scripts/docker-compose.yml restart mongodb
```

### Redis Connection Issues

```bash
# Check if Redis is running
docker ps | grep redis
# On Windows PowerShell:
docker ps | Select-String redis

# Test Redis connection
docker exec -it spur_redis redis-cli ping
```

### LLM API Errors

- Verify `GOOGLE_API_KEY` is set correctly in `.env`
- Check that `GOOGLE_MODEL` matches an available model (e.g., `gemini-2.5-flash`, `gemini-3-flash`)
- Verify API key is valid at: https://makersuite.google.com/app/apikey
- Check API quota/limits in Google AI Studio
- Review error logs in backend console

### Frontend Not Connecting to Backend

- Verify backend is running on port 8000
- Check `VITE_API_URL` in frontend `.env`
- Check CORS settings in `backend/app/main.py`
- Check browser console for errors

### Seed Script Issues

**Error running `python scripts/seed_faqs.py`:**
- Ensure you're in the `backend` directory
- Ensure virtual environment is activated
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Ensure MongoDB is running: `docker ps | grep mongodb`

## License

This is a take-home assignment project for Spur.

## Contact

For questions or issues, please refer to the assignment submission form.

