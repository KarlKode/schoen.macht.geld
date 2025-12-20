# Backend

FastAPI backend for the Schön. Macht. Geld. stock exchange party game.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
cp .env.example .env
uv sync
```

## Run

```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload
```

Server runs at http://localhost:8000. API docs at `/docs`. Admin panel at `/admin/`.

## Project Structure

```
src/app/
├── main.py           # Application entry point
├── config.py         # Settings (env vars)
├── database.py       # SQLite async connection
├── storage.py        # Image storage with validation & compression
├── scheduler.py      # Background jobs (price ticks, snapshots)
├── admin.py          # Admin panel (SQLAdmin)
├── models/           # SQLModel database models
├── schemas/          # Pydantic request/response schemas
├── routers/          # API endpoints
└── services/         # External services (AtlasCloud, Google AI)
data/
├── stocks.db         # SQLite database (auto-created)
└── images/           # Uploaded stock images
```

## Data Models

### Stock

| Field | Type | Description |
|-------|------|-------------|
| ticker | str | Primary key (e.g. "APPL") |
| title | str | Display name |
| image | str? | Image path (served at `/images/`) |
| description | str | Profile description |
| is_active | bool | Whether stock is tradeable |
| price | float | Current price |
| rank | int? | Rank by price (1 = highest) |
| change_rank | int? | Rank by % change (1 = top gainer) |

### PriceEvent

| Field | Type | Description |
|-------|------|-------------|
| id | int | Auto-increment primary key |
| ticker | str | Foreign key to Stock |
| price | float | Price after change |
| change_type | enum | initial, swipe_up, swipe_down, random, admin |
| created_at | datetime | Timestamp |

### StockSnapshot

Used for price history charts.

| Field | Type | Description |
|-------|------|-------------|
| id | int | Auto-increment primary key |
| ticker | str | Foreign key to Stock |
| price | float | Price at snapshot time |
| created_at | datetime | Timestamp |

## API Reference

Full interactive docs at `/docs` (Swagger UI).

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /stocks/ | List stocks (?random, ?limit) |
| POST | /stocks/ | Create stock |
| GET | /stocks/{ticker} | Get stock by ticker |
| POST | /stocks/{ticker}/image | Upload stock image |
| POST | /stocks/{ticker}/price | Adjust price (admin) |
| GET | /stocks/{ticker}/snapshots | Price history |
| GET | /stocks/{ticker}/events | Price change log |
| POST | /swipe/ | Record swipe vote |

### AI Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /ai/generate/description | Generate stock description |
| POST | /ai/generate/headlines | Generate news headlines |
| POST | /ai/generate/image | Generate stock image |
| POST | /ai/generate/video | Generate ad video |
| GET | /ai/tasks | List AI tasks |
| GET | /ai/tasks/{id} | Get task status |
| POST | /ai/tasks/{id}/apply | Apply result to stock |
| DELETE | /ai/tasks/{id} | Delete task |

### API Examples

**Create stock:**

```bash
# Without image
curl -X POST http://localhost:8000/stocks/ \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TEST", "title": "Test Stock"}'

# With image
curl -X POST http://localhost:8000/stocks/ \
  -F 'ticker=TEST' \
  -F 'title=Test Stock' \
  -F 'image=@photo.jpg'
```

**Upload/replace image:**

```bash
curl -X POST http://localhost:8000/stocks/TEST/image \
  -F 'image=@photo.jpg'
```

**Adjust price:**

```bash
curl -X POST http://localhost:8000/stocks/TEST/price \
  -H "Content-Type: application/json" \
  -d '{"delta": 50.0, "change_type": "admin"}'
```

**Submit swipe:**

```bash
curl -X POST http://localhost:8000/swipe/ \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TEST", "direction": "right", "swipe_token": null}'
```

**Generate AI content:**

```bash
# Generate description
curl -X POST http://localhost:8000/ai/generate/description \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TEST"}'

# Check task status
curl http://localhost:8000/ai/tasks/{task_id}

# Apply result
curl -X POST http://localhost:8000/ai/tasks/{task_id}/apply \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TEST"}'
```

## Swipe Token System

Swipes use a stateless token to track user behavior without sessions. The token is a base64-encoded JSON:

```json
{"ts": 1703001234, "buckets": [[3, 1], [2, 4], ...]}
```

Features:
- **Streak detection**: Consecutive same-direction swipes reduce impact (0.7x after 5+)
- **Pickiness bonus**: Users who swipe left often get bonus on right swipes
- **Time decay**: Old swipe data expires automatically

Price formula:
```
base = price * random(1-3%)
final = base * streak_penalty * pickiness_bonus * random(0.5-2.0) * direction
```

## Admin Panel

Access at `/admin/`. Features:

- **Stocks**: View, create, edit, delete, search (supports camera capture on mobile)
- **Price Events**: View price change history (read-only)
- **Stock Snapshots**: View periodic snapshots (read-only)
- **AI Tasks**: View generation tasks and status

## Background Jobs

The scheduler runs automatically:

| Job | Interval | Description |
|-----|----------|-------------|
| Price Tick | 60s | Random ±5% price changes |
| Snapshots | 60s | Capture prices, calculate rankings |
| AI Tasks | 10s | Poll and process AI generation |

## Image Handling

- **Formats**: JPEG, PNG, GIF, WebP, AVIF, HEIC/HEIF, BMP
- **Max size**: 20MB
- **Auto-processing**: Resize to 1920px max, convert to JPEG, compress to 85%
- **Cleanup**: Old images deleted when replaced

HEIC/HEIF support via `pillow-heif` for iPhone photos.

## AI Content Generation

Requires AtlasCloud API key. Google AI available as fallback for text.

| Type | Model | Cost |
|------|-------|------|
| Text | google/gemini-3-flash-preview | Free |
| Image | black-forest-labs/flux-schnell | $0.003/img |
| Video | alibaba/wan-2.2/t2v-480p | $0.009/sec |

## Database Migrations

```bash
uv run alembic upgrade head          # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create migration
uv run alembic downgrade -1          # Rollback
```

## Configuration

All settings via environment variables or `.env` file.

### Server

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite+aiosqlite:///./data/stocks.db | Database path |
| UVICORN_HOST | 127.0.0.1 | Bind address |
| UVICORN_PORT | 8000 | Server port |
| UVICORN_WORKERS | 1 | Worker processes |
| ROOT_PATH | | Set to `/api` behind proxy |
| CORS_ALLOW_ALL | false | Allow all origins (dev) |

### Pricing

| Variable | Default | Description |
|----------|---------|-------------|
| STOCK_BASE_PRICE | 1000.0 | Initial stock price |
| PRICE_TICK_INTERVAL | 60 | Seconds between random ticks |
| PRICE_TICK_ENABLED | true | Enable random price updates |
| SNAPSHOT_INTERVAL | 60 | Seconds between snapshots |
| SNAPSHOT_RETENTION | 30 | Snapshots to keep per stock |

### Images

| Variable | Default | Description |
|----------|---------|-------------|
| IMAGE_DIR | ./data/images | Storage path |
| MAX_IMAGE_SIZE | 20971520 | Max upload size (bytes) |
| IMAGE_MAX_DIMENSION | 1920 | Max width/height |
| IMAGE_QUALITY | 85 | JPEG quality (1-100) |

### AI

| Variable | Default | Description |
|----------|---------|-------------|
| ATLASCLOUD_API_KEY | | Required for AI features |
| ATLASCLOUD_TEXT_MODEL | google/gemini-3-flash-preview | Text model |
| ATLASCLOUD_IMAGE_MODEL | black-forest-labs/flux-schnell | Image model |
| GOOGLE_AI_API_KEY | | Fallback for text |
| FORCE_GOOGLE_AI | false | Always use Google AI |

### Swipe

| Variable | Default | Description |
|----------|---------|-------------|
| SWIPE_BUCKET_DURATION | 20 | Seconds per history bucket |
| SWIPE_BUCKET_COUNT | 30 | Number of buckets |
| SWIPE_BASE_PERCENT_MIN | 0.01 | Min price change (1%) |
| SWIPE_BASE_PERCENT_MAX | 0.03 | Max price change (3%) |
| SWIPE_STREAK_THRESHOLD | 5 | Buckets for streak detection |
| SWIPE_STREAK_PENALTY | 0.7 | Multiplier when streak detected |

## Development

```bash
uv run ruff check src/        # Lint
uv run basedpyright src/      # Type check
uv run pytest                 # Test
```
