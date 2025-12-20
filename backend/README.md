# Backend

FastAPI backend for the Schoen Macht Geld stock exchange party game.

## Requirements

- Python 3.14+
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
   storage.py        # Image storage with validation & unique filenames
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

| Field             | Type          | Description                              |
|-------------------|---------------|------------------------------------------|
| ticker            | str           | Primary key (4 chars, e.g. "AAPL")       |
| title             | str           | Display name                             |
| image             | StorageImage? | Uploaded image (served at `/images/`)    |
| description       | str           | Optional description                     |
| is_active         | bool          | Whether stock is tradeable               |
| price             | float         | Current price (from latest StockPrice)   |
| reference_price   | float?        | Price at last snapshot (for % change)    |
| reference_price_at| datetime?     | When reference price was set             |
| percentage_change | float?        | Change from reference price (computed)   |
| prices            | list          | Price history entries                    |
| snapshots         | list          | Periodic price snapshots for graphs      |

### StockPrice

| Field       | Type       | Description                    |
|-------------|------------|--------------------------------|
| id          | int        | Auto-increment primary key     |
| ticker      | str        | Foreign key to Stock           |
| price       | float      | Price at this point in time    |
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
| POST   | /swipe/                     | Record swipe action            |
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

**Note:** Price history is limited to the 10 most recent entries per stock to reduce response size.

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

- **Allowed types**: JPEG, PNG, GIF, WebP
- **Max size**: 5MB (configurable via `MAX_IMAGE_SIZE`)

### Unique Filenames

Uploaded files are prefixed with a 12-character UUID to prevent collisions:
```
a1b2c3d4e5f6_original_filename.jpg
```

This allows different stocks to upload files with the same original name without overwriting each other.

### Old Image Cleanup

When replacing a stock's image (via API or admin panel), the old image file is automatically deleted from disk after the new one is saved.

### Manipulate Price

```bash
curl -X POST http://localhost:8000/stocks/APPL/price \
  -H "Content-Type: application/json" \
  -d '{"delta": 5.0, "change_type": "admin"}'
```

## Admin Panel

Access at `/admin`. Features:

- **Stocks**: View, create, edit, search stocks (supports camera capture on mobile)
- **Stock Prices**: View price history (read-only)
- **Stock Snapshots**: View periodic price snapshots (read-only)
- **AI Tasks**: View AI generation tasks and their status

## Background Scheduler

The scheduler runs several background jobs:

### Price Tick
Periodically applies random price changes (±5%) to all active stocks.

- `PRICE_TICK_INTERVAL` - Seconds between updates (default: 60)
- `PRICE_TICK_ENABLED` - Enable/disable (default: true)

### Price Snapshots
Periodically captures price snapshots for line graphs and percentage change calculation.
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
| CORS_ORIGINS        | ["http://localhost:3000"]            | Allowed CORS origins               |
| LOGURU_LEVEL        | INFO                                 | Log level (loguru)                 |
| STOCK_BASE_PRICE    | 1000.0                               | Default price for new stocks       |
| PRICE_TICK_INTERVAL | 60                                   | Seconds between random price ticks |
| PRICE_TICK_ENABLED  | true                                 | Enable background price updates    |
| SNAPSHOT_INTERVAL   | 60                                   | Seconds between price snapshots    |
| SNAPSHOT_RETENTION  | 30                                   | Snapshots to keep per stock        |
| IMAGE_DIR           | ./data/images                        | Directory for uploaded images      |
| MAX_IMAGE_SIZE      | 5242880                              | Max image upload size (bytes)      |
| ATLASCLOUD_API_KEY  | (required for AI)                    | AtlasCloud API key                 |
| ATLASCLOUD_TEXT_MODEL | google/gemini-3-flash-preview-developer | Text generation model     |
| ATLASCLOUD_IMAGE_MODEL | black-forest-labs/flux-schnell    | Image generation model             |
| ATLASCLOUD_VIDEO_T2V_MODEL | alibaba/wan-2.2/t2v-480p-ultra-fast | Text-to-video model        |
| AI_TASK_POLL_INTERVAL | 10                                 | Seconds between AI task polls      |
| AI_TASK_TIMEOUT     | 300                                  | Max seconds for AI task completion |

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

| Old Field       | New Field      | Notes                           |
|-----------------|----------------|---------------------------------|
| `nickname`      | `title`        | Renamed                         |
| `photo_url`     | `image`        | Now `StorageImage?` (file upload only) |
| `current_value` | `price`        | Computed from latest StockPrice |
| `initial_value` | `initial_price`| Computed from first StockPrice  |
| `rank`          | -              | Removed                         |
| `previous_rank` | -              | Removed                         |
| `history`       | `prices`       | Renamed                         |
| -               | `is_active`    | New field (boolean)             |

### StockPrice (formerly PriceHistory) Changes

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
  - Allowed types: JPEG, PNG, GIF, WebP
  - Max size: 5MB
  - Returns: Stock with `image` path (served at `/images/`)

- `POST /stocks/{ticker}/price` - Manipulate stock price
  - Body: `{ "delta": float, "change_type": "admin" | "random" | ... }`
