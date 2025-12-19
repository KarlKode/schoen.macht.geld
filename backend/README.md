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

| Field       | Type          | Description                           |
|-------------|---------------|---------------------------------------|
| ticker      | str           | Primary key (4 chars, e.g. "AAPL")    |
| title       | str           | Display name                          |
| image       | StorageImage? | Uploaded image (served at `/images/`) |
| description | str           | Optional description                  |
| is_active   | bool          | Whether stock is tradeable            |
| price       | float         | Current price (from latest StockPrice)|
| prices      | list          | Price history entries                 |

### StockPrice

| Field       | Type       | Description                    |
|-------------|------------|--------------------------------|
| id          | int        | Auto-increment primary key     |
| ticker      | str        | Foreign key to Stock           |
| price       | float      | Price at this point in time    |
| change_type | ChangeType | Why the price changed          |
| created_at  | datetime   | Timestamp                      |

### ChangeType Enum

- `initial` - Stock creation
- `swipe_up` - User swiped right
- `swipe_down` - User swiped left
- `random` - Periodic background update
- `admin` - Manual adjustment

## API Endpoints

| Method | Path                    | Description              |
|--------|-------------------------|--------------------------|
| GET    | /health                 | Health check             |
| GET    | /stocks/                | List all stocks          |
| POST   | /stocks/                | Create new stock         |
| GET    | /stocks/{ticker}        | Get stock by ticker      |
| POST   | /stocks/{ticker}/image  | Upload stock image       |
| POST   | /stocks/{ticker}/price  | Manipulate stock price   |
| POST   | /swipe/                 | Record swipe action      |
| GET    | /images/{filename}      | Serve uploaded images    |

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

- **Stocks**: View, create, edit, search stocks
- **Stock Prices**: View price history (read-only)

## Background Scheduler

When enabled, the scheduler periodically applies random price changes (±5%) to all active stocks. Configure via:

- `PRICE_TICK_INTERVAL` - Seconds between updates (default: 60)
- `PRICE_TICK_ENABLED` - Enable/disable (default: true)

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
| IMAGE_DIR           | ./data/images                        | Directory for uploaded images      |
| MAX_IMAGE_SIZE      | 5242880                              | Max image upload size (bytes)      |

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
