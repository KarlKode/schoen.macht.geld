# Backend

FastAPI backend for the Schoen Macht Geld stock exchange party game.

## Requirements

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

## Setup

```bash
cp .env.example .env
# review .env and adjust as needed
uv sync
```

## Run

```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`. API docs at `/docs`. Admin panel at `/admin`.

## Project Structure

```
src/app/
   main.py           # Application entry point
   config.py         # Settings (env vars)
   database.py       # SQLite async connection
   storage.py        # Image storage with validation & compression
   scheduler.py      # Background price tick scheduler
   admin.py          # Admin panel configuration
   models/           # SQLModel database models
   schemas/          # Pydantic request/response schemas
   routers/          # API endpoints
data/
   stocks.db         # SQLite database (auto-created)
   images/           # Uploaded stock images
```

## Data Models

### Stock

| Field               | Type          | Description                              |
|---------------------|---------------|------------------------------------------|
| ticker              | str           | Primary key (4 chars, e.g. "AAPL")       |
| title               | str           | Display name                             |
| image               | StorageImage? | Uploaded image (served at `/images/`)    |
| description         | str           | Optional description                     |
| is_active           | bool          | Whether stock is tradeable               |
| price               | float         | Current price (from latest PriceEvent)   |
| reference_price     | float?        | Price at last snapshot (for % change)    |
| reference_price_at  | datetime?     | When reference price was set             |
| percentage_change   | float?        | Change from reference price (computed)   |
| rank                | int?          | Current rank by price (1 = highest)      |
| previous_rank       | int?          | Rank at previous snapshot                |
| rank_change         | int?          | Places gained/lost (positive = up)       |
| change_rank         | int?          | Current rank by % change (1 = top gainer)|
| previous_change_rank| int?          | Change rank at previous snapshot         |
| change_rank_change  | int?          | Places gained/lost (positive = up)       |
| price_events        | list          | Price change event log                   |
| snapshots           | list          | Periodic price snapshots for graphs      |

### PriceEvent

Price change event log - captures every price change with its cause.

| Field       | Type       | Description                    |
|-------------|------------|--------------------------------|
| id          | int        | Auto-increment primary key     |
| ticker      | str        | Foreign key to Stock           |
| price       | float      | Price after this change        |
| change_type | ChangeType | Why the price changed          |
| created_at  | datetime   | Timestamp                      |

### StockSnapshot

Periodic price snapshots used for line graphs and percentage change calculation.

| Field       | Type     | Description                |
|-------------|----------|----------------------------|
| id          | int      | Auto-increment primary key |
| ticker      | str      | Foreign key to Stock       |
| price       | float    | Price at snapshot time     |
| created_at  | datetime | Timestamp                  |

### ChangeType Enum

- `initial` - Stock creation
- `swipe_up` - User swiped right
- `swipe_down` - User swiped left
- `random` - Periodic background update
- `admin` - Manual adjustment

## API Endpoints

| Method | Path                        | Description                    |
|--------|-----------------------------|--------------------------------|
| GET    | /health                     | Health check                   |
| GET    | /stocks/                    | List all stocks                |
| POST   | /stocks/                    | Create new stock               |
| GET    | /stocks/{ticker}            | Get stock by ticker            |
| POST   | /stocks/{ticker}/image      | Upload stock image             |
| POST   | /stocks/{ticker}/price      | Manipulate stock price         |
| GET    | /stocks/{ticker}/snapshots  | Get price snapshots for graphs |
| GET    | /stocks/{ticker}/events     | Get price change event log     |
| POST   | /swipe/                     | Record swipe action (with token)|
| GET    | /images/{filename}          | Serve uploaded images          |

### List Stocks Query Parameters

| Parameter | Type  | Default | Description                    |
|-----------|-------|---------|--------------------------------|
| random    | bool  | false   | Randomize stock order          |
| limit     | int   | null    | Limit number of stocks returned|

Example: Get 5 random stocks:
```bash
curl "http://localhost:8000/stocks/?random=true&limit=5"
```

**Note:** Price events are limited to the 10 most recent entries per stock to reduce response size.

### Create Stock

```bash
# Without image
curl -X POST http://localhost:8000/stocks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Apple"}'

# With image (multipart/form-data)
curl -X POST http://localhost:8000/stocks/ \
  -F 'request={"title": "Apple"};type=application/json' \
  -F "image=@photo.jpg"
```

### Upload Image

```bash
curl -X POST http://localhost:8000/stocks/APPL/image \
  -F "image=@photo.jpg"
```

## Image Handling

Images are stored locally in `./data/images/` and served at `/images/{filename}`.

### Validation

- **Allowed types**: JPEG, PNG, GIF, WebP, AVIF, HEIC/HEIF, BMP
- **Max size**: 20MB (configurable via `MAX_IMAGE_SIZE`)

HEIC/HEIF support is provided by `pillow-heif` for iPhone photos.

### Automatic Compression

All uploaded images are automatically processed:

1. **Resize**: Images larger than 1920px (configurable) are resized to fit
2. **Convert**: All formats converted to JPEG for optimal compression
3. **Compress**: JPEG quality 85% (configurable) with optimization

This typically reduces file sizes by 50-90%, e.g., a 5MB phone photo → ~200KB.

### Old Image Cleanup

When replacing a stock's image (via API or admin panel), the old image file is automatically deleted from disk after the new one is saved.

### Manipulate Price

```bash
curl -X POST http://localhost:8000/stocks/APPL/price \
  -H "Content-Type: application/json" \
  -d '{"delta": 5.0, "change_type": "admin"}'
```

## Swipe Endpoint

The swipe endpoint uses a stateless token system to track user behavior without requiring login or session storage.

### Request

```bash
curl -X POST http://localhost:8000/swipe/ \
  -H "Content-Type: application/json" \
  -d '{"ticker": "APPL", "direction": "right", "swipe_token": null}'
```

| Field        | Type        | Description                          |
|--------------|-------------|--------------------------------------|
| ticker       | str         | Stock ticker to swipe on             |
| direction    | "left"/"right" | Swipe direction                   |
| swipe_token  | str?        | Token from previous response (or null)|

### Response

```json
{
  "ticker": "APPL",
  "new_price": 1025.50,
  "delta": 25.50,
  "swipe_token": "eyJ0cyI6MTcwMzAwMTIzNCwiYnVja2V0cyI6W1sxLDBdXX0="
}
```

| Field        | Type  | Description                     |
|--------------|-------|---------------------------------|
| ticker       | str   | Stock ticker                    |
| new_price    | float | Price after swipe               |
| delta        | float | Actual price change applied     |
| swipe_token  | str   | Token to send with next request |

### How Swipe Tokens Work

The token is a base64-encoded JSON containing bucketed swipe history:

```json
{
  "ts": 1703001234,
  "buckets": [[3, 1], [2, 4], [0, 0], ...]
}
```

- `ts`: Timestamp of last update
- `buckets`: Array of `[left_count, right_count]` per time interval

The frontend stores the token and sends it with each swipe. The backend uses this to:

1. **Track streaks**: Consecutive same-direction swipes reduce impact
2. **Measure pickiness**: Users who swipe left often get bonus on right swipes
3. **Expire old data**: Buckets shift over time, old data drops off

### Price Calculation

Price changes use a hybrid approach:

```
base_change = current_price * random(1-3%)
modifiers:
  - streak_penalty: 0.7x if 5+ consecutive same direction
  - pickiness_bonus: up to 1.5x for picky users (many left swipes)
  - random_multiplier: 0.5x to 2.0x
final_delta = base_change * modifiers * direction
```

## Admin Panel

Access at `/admin`. Features:

- **Stocks**: View, create, edit, search stocks (supports camera capture on mobile)
- **Price Events**: View price change event log (read-only)
- **Stock Snapshots**: View periodic price snapshots (read-only)
- **AI Tasks**: View AI generation tasks and their status

## Background Scheduler

The scheduler runs several background jobs:

### Price Tick
Periodically applies random price changes (±5%) to all active stocks.

- `PRICE_TICK_INTERVAL` - Seconds between updates (default: 60)
- `PRICE_TICK_ENABLED` - Enable/disable (default: true)

### Price Snapshots & Rankings
Periodically captures price snapshots and calculates rankings for all active stocks.

Each snapshot:
1. Updates `reference_price` for percentage change calculation
2. Creates a `StockSnapshot` entry for graph history
3. Calculates rankings by price (`rank`) and by percentage change (`change_rank`)
4. Tracks places gained/lost (`rank_change`, `change_rank_change`)

Snapshots are automatically cleaned up to keep only the most recent N per stock.

- `SNAPSHOT_INTERVAL` - Seconds between snapshots (default: 60)
- `SNAPSHOT_RETENTION` - Number of snapshots to keep per stock (default: 30)

The `percentage_change` field on stocks shows change from the last snapshot (like Yahoo Finance's daily change).

## AI Content Generation

Generate absurd/funny stock content using [AtlasCloud](https://www.atlascloud.ai/) AI APIs. Requires an API key.

### Features

- **Description Generation**: Create satirical stock descriptions
- **Image Generation**: Generate logos, billboards, website mockups, and main images
- **Video Generation**: Create short advertisement clips

### AI Endpoints

| Method | Path                      | Description                    |
|--------|---------------------------|--------------------------------|
| POST   | /ai/generate/description  | Generate stock description     |
| POST   | /ai/generate/image        | Generate stock image           |
| POST   | /ai/generate/video        | Generate advertisement video   |
| GET    | /ai/tasks                 | List all AI tasks              |
| GET    | /ai/tasks/{task_id}       | Get task status and result     |
| POST   | /ai/tasks/{task_id}/apply | Apply result to stock          |
| DELETE | /ai/tasks/{task_id}       | Delete task                    |

### Example Usage

```bash
# Generate a description for a stock
curl -X POST http://localhost:8000/ai/generate/description \
  -H "Content-Type: application/json" \
  -d '{"ticker": "APPL"}'

# Generate an image (logo type)
curl -X POST http://localhost:8000/ai/generate/image \
  -H "Content-Type: application/json" \
  -d '{"ticker": "APPL", "image_type": "logo"}'

# Check task status
curl http://localhost:8000/ai/tasks/{task_id}

# Apply generated description to stock
curl -X POST http://localhost:8000/ai/tasks/{task_id}/apply \
  -H "Content-Type: application/json" \
  -d '{"ticker": "APPL"}'
```

### How It Works

1. API request creates an `AITask` in pending status
2. Background scheduler picks up pending tasks
3. Task is submitted to AtlasCloud API
4. Scheduler polls for completion
5. Results are downloaded and stored locally
6. Client polls `/ai/tasks/{id}` for status

### Models Used

| Type  | Default Model                           | Cost        |
|-------|----------------------------------------|-------------|
| Text  | google/gemini-3-flash-preview-developer | FREE        |
| Image | black-forest-labs/flux-schnell          | $0.00255/img|
| Video | alibaba/wan-2.2/t2v-480p-ultra-fast     | $0.0085/sec |

Override via environment variables or pass `model` parameter in requests.

## Configuration

Environment variables (or `.env` file):

| Variable            | Default                              | Description                        |
|---------------------|--------------------------------------|------------------------------------|
| DATABASE_URL        | sqlite+aiosqlite:///./data/stocks.db | SQLite database path               |
| DEBUG               | false                                | Enable debug mode                  |
| CORS_ORIGINS        | ["http://localhost:3000"]            | Allowed CORS origins (JSON array)  |
| CORS_ALLOW_ALL      | false                                | Allow all origins (dev only!)      |
| UVICORN_HOST        | 127.0.0.1                            | Server bind address                |
| UVICORN_PORT        | 8000                                 | Server port                        |
| UVICORN_WORKERS     | 1                                    | Number of worker processes         |
| LOGURU_LEVEL        | INFO                                 | Log level (loguru)                 |
| STOCK_BASE_PRICE    | 1000.0                               | Default price for new stocks       |
| PRICE_TICK_INTERVAL | 60                                   | Seconds between random price ticks |
| PRICE_TICK_ENABLED  | true                                 | Enable background price updates    |
| SNAPSHOT_INTERVAL   | 60                                   | Seconds between price snapshots    |
| SNAPSHOT_RETENTION  | 30                                   | Snapshots to keep per stock        |
| IMAGE_DIR           | ./data/images                        | Directory for uploaded images      |
| MAX_IMAGE_SIZE      | 20971520                             | Max image upload size (bytes)      |
| IMAGE_MAX_DIMENSION | 1920                                 | Max width/height after resize      |
| IMAGE_QUALITY       | 85                                   | JPEG compression quality (1-100)   |
| ATLASCLOUD_API_KEY  | (required for AI)                    | AtlasCloud API key                 |
| ATLASCLOUD_TEXT_MODEL | google/gemini-3-flash-preview-developer | Text generation model     |
| ATLASCLOUD_IMAGE_MODEL | black-forest-labs/flux-schnell    | Image generation model             |
| ATLASCLOUD_VIDEO_T2V_MODEL | alibaba/wan-2.2/t2v-480p-ultra-fast | Text-to-video model        |
| AI_TASK_POLL_INTERVAL | 10                                 | Seconds between AI task polls      |
| AI_TASK_TIMEOUT     | 300                                  | Max seconds for AI task completion |
| SWIPE_BUCKET_DURATION | 20                                 | Seconds per swipe history bucket   |
| SWIPE_BUCKET_COUNT  | 30                                   | Number of buckets (~10 min history)|
| SWIPE_BASE_PERCENT_MIN | 0.01                              | Min base price change (1%)         |
| SWIPE_BASE_PERCENT_MAX | 0.03                              | Max base price change (3%)         |
| SWIPE_RANDOM_MULTIPLIER_MIN | 0.5                         | Min random multiplier              |
| SWIPE_RANDOM_MULTIPLIER_MAX | 2.0                         | Max random multiplier              |
| SWIPE_STREAK_THRESHOLD | 5                                 | Buckets for streak detection       |
| SWIPE_STREAK_PENALTY | 0.7                                 | Multiplier when streak detected    |

## Production Deployment

### Docker Compose (Recommended)

The easiest way to run in production - handles auto-restart, Caddy reverse proxy, and all services.

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Rebuild after code changes
docker compose build && docker compose up -d
```

This starts:
- **backend** - Python/uvicorn on port 8000 (internal)
- **caddy** - Reverse proxy on ports 80/443
- **backup** - Periodic backup service (every 10 minutes)

Data is persisted in `./data/` (database + images). Backups are written to `./backups/`.

#### Database Migrations

The project uses Alembic for database migrations:

```bash
# Run migrations (creates/updates tables)
uv run alembic upgrade head

# In Docker
docker compose exec backend alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Check current migration status
uv run alembic current

# Rollback one migration
uv run alembic downgrade -1
```

Note: On first startup, `init_db()` creates tables automatically using SQLModel. Migrations are primarily for schema changes after initial deployment.

#### Auto-start on Boot

Docker automatically restarts containers after reboot (due to `restart: unless-stopped`). Just ensure Docker starts on boot:

```bash
# Linux
sudo systemctl enable docker

# macOS - Docker Desktop starts automatically

# Windows - Docker Desktop starts automatically
```

#### Custom Domain with HTTPS

Edit `Caddyfile` to use your domain:
```
stock.party.example.com {
    handle /images/* {
        root * /srv
        file_server
    }
    handle {
        reverse_proxy backend:8000
    }
}
```

Caddy automatically provisions Let's Encrypt certificates.

#### Backup & Disaster Recovery

The backup container creates consistent snapshots every 10 minutes:

```
┌─────────────────┐     ┌─────────────────┐
│   App Container │     │ Backup Container│
│                 │     │   (10 min loop) │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
    ┌─────────┐            ┌──────────┐
    │ ./data  │───(ro)────▶│ /data    │
    │ (live)  │            │          │
    └─────────┘            └────┬─────┘
                                │ sqlite3 .backup
                                │ rsync
                                ▼
                          ┌──────────┐
                          │./backups │◀──── External machine pulls
                          │ (staged) │
                          └──────────┘
```

**How it works:**
- Uses `sqlite3 .backup` for atomic, corruption-safe database snapshots
- Uses `rsync` to sync images/videos
- Mounts `./data` as read-only to avoid interference with live data
- Writes to `./backups/` which can be a different drive/mount

**Pulling backups to your MacBook:**

Set up SSH key auth from your Mac to the Pi, then run this script periodically (via cron or launchd):

```bash
#!/bin/bash
# pull-backup.sh - Run on MacBook

RASPBI="pi@raspberrypi.local:/path/to/schoen.macht.geld/backend/backups/"
LOCAL="$HOME/party-backups/"

rsync -az "$RASPBI" "$LOCAL"
```

**Recovery (if Pi dies mid-party):**

```bash
# On MacBook
cd /path/to/schoen.macht.geld/backend
cp ~/party-backups/stocks.db ./data/
cp -r ~/party-backups/images/* ./data/images/
docker compose up -d
```

Then either update DNS/hosts on phones or port-forward from Pi to MacBook.

**Using a different backup drive:**

Mount an external drive to `./backups`:
```yaml
# docker-compose.yml
backup:
  volumes:
    - ./data:/data:ro
    - /mnt/usb-backup:/backups  # External drive
```

### Manual Deployment (without Docker)

Development (with hot reload):
```bash
PYTHONPATH=src uv run uvicorn app.main:app --reload
```

Production (using config from .env):
```bash
PYTHONPATH=src uv run python -m app
```

Or with explicit settings:
```bash
PYTHONPATH=src uv run uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

#### Caddy Reverse Proxy (Manual)

If running without Docker, install Caddy separately and use this config:

```
stock.party.local {
    handle /images/* {
        root * /path/to/backend/data
        file_server
    }
    handle {
        reverse_proxy localhost:8000
    }
}
```

Update `.env` for production:
```bash
CORS_ORIGINS=["https://stock.party.local"]
UVICORN_HOST=127.0.0.1  # Only listen on localhost, Caddy proxies
UVICORN_PORT=8000
UVICORN_WORKERS=4
```

## Development

```bash
uv run ruff check src/
uv run basedpyright src/
uv run pytest
```

---

## Frontend Migration Notes

The following changes need to be made in the frontend:

### Stock Model Changes

| Old Field       | New Field       | Notes                              |
|-----------------|-----------------|-------------------------------------|
| `nickname`      | `title`         | Renamed                             |
| `photo_url`     | `image`         | Now `StorageImage?` (file upload)   |
| `current_value` | `price`         | Computed from latest PriceEvent     |
| `initial_value` | `initial_price` | Computed from first PriceEvent      |
| `rank`          | `rank`          | Now computed by snapshot scheduler  |
| `previous_rank` | `previous_rank` | Now computed by snapshot scheduler  |
| `history`       | `price_events`  | Renamed                             |
| -               | `is_active`     | New field (boolean)                 |

### PriceEvent (formerly PriceHistory) Changes

| Old Field   | New Field     | Notes                      |
|-------------|---------------|----------------------------|
| `value`     | `price`       | Renamed                    |
| `timestamp` | `created_at`  | Renamed                    |
| -           | `id`          | New field (auto-increment) |
| -           | `change_type` | New field (enum)           |

### StockCreate Request Changes

| Old Field   | New Field       | Notes                              |
|-------------|-----------------|-------------------------------------|
| `nickname`  | `title`         | Renamed                             |
| `photo_url` | -               | Removed (use file upload endpoint)  |
| -           | `initial_price` | New field (default: STOCK_BASE_PRICE)|

### New Endpoints

- `POST /stocks/{ticker}/image` - Upload stock image file
  - Content-Type: `multipart/form-data`
  - Field: `image` (image file)
  - Allowed types: JPEG, PNG, GIF, WebP, AVIF, HEIC/HEIF, BMP
  - Max size: 20MB
  - Returns: Stock with `image` path (served at `/images/`)

- `POST /stocks/{ticker}/price` - Manipulate stock price
  - Body: `{ "delta": float, "change_type": "admin" | "random" | ... }`
