# Schön. Macht. Geld.

A satirical stock market party game where guests become publicly traded "stocks." Their market value fluctuates in real-time based on swipes from other guests.

## The Concept

1. **Become a Stock:** A guest registers at a kiosk with a nickname and photo, becoming a tradeable "stock" with an initial value.
2. **Influence the Market:** Other guests swipe right (like) or left (dislike) on profiles, directly affecting stock prices.
3. **Live Market Data:** Display screens show real-time tickers, leaderboards, market maps, and AI-generated satirical news headlines.

The theme is a satirical take on finance culture, vanity, and social climbing within a hedonistic party setting. Created by the "Verein für ambitionierten Konsum (VAK)" and "Amphitheater" Zürich.

## Quick Start

```bash
# Clone and configure
git clone <repo-url>
cd schoen.macht.geld
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker compose up -d
```

Access at http://localhost:8080 (or configure ports in `docker-compose.yml`)

**Seed demo data (optional):**

```bash
# Run seed script against running backend
curl -X POST http://localhost:8080/api/stocks/ \
  -F 'ticker=DEMO' \
  -F 'title=Demo Stock' \
  -F 'initial_price=100'
```

Or use the admin panel at http://localhost:8080/admin/

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Caddy                                │
│                   (Reverse Proxy + TLS)                      │
│                      Port 80/443                             │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
           │ /api/*                         │ /*
           ▼                                ▼
┌──────────────────────┐          ┌──────────────────────┐
│       Backend        │          │      Frontend        │
│   (FastAPI/Python)   │          │   (Next.js/React)    │
│      Port 8000       │          │      Port 3000       │
└──────────┬───────────┘          └──────────────────────┘
           │
           ▼
┌──────────────────────┐
│   SQLite Database    │
│   + Image Storage    │
└──────────────────────┘
```

## Interfaces

| Route | Purpose | Target Hardware |
|-------|---------|-----------------|
| `/swipe` | Swipe voting interface | Touchscreen phones/tablets |
| `/display` | Stock ticker | Large screens / Raspberry Pi |
| `/display/leaderboard` | Top stocks ranking | Large screens |
| `/display/market-map` | Visual market overview | Large screens |
| `/display/stock-chart` | Price history charts | Large screens |
| `/display/terminal` | News ticker + headlines | Large screens |
| `/admin/` | Stock management | Any browser |

## Tech Stack

- **Frontend:** Next.js 15, React 18, TypeScript, Tailwind CSS, ShadCN UI, SWR
- **Backend:** FastAPI, SQLModel, SQLite, APScheduler
- **AI:** AtlasCloud API (text/image/video), Google AI (fallback)
- **Infrastructure:** Docker Compose, Caddy (reverse proxy + auto-HTTPS)

## Development

### Backend

```bash
cd backend
cp .env.example .env
uv sync
PYTHONPATH=src uv run uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs, Admin at http://localhost:8000/admin/

### Frontend

```bash
cd frontend
pnpm install
NEXT_PUBLIC_API_URL=http://localhost:8000 pnpm dev
```

Runs at http://localhost:3000

### Regenerate API Client

After backend API changes:

```bash
cd frontend
pnpm generate-api
```

## Production Deployment

### Docker Compose

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after changes
docker compose build && docker compose up -d

# Stop
docker compose down
```

Services:
- **backend** - FastAPI on port 8000 (internal)
- **frontend** - Next.js on port 3000 (internal)
- **caddy** - Reverse proxy on ports 80/443
- **backup** - SQLite snapshots every 10 minutes

### Custom Domain with HTTPS

Edit `Caddyfile`:

```
smg.example.com {
    handle /images/* {
        root * /srv
        file_server
    }
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy backend:8000
    }
    handle /admin/* {
        reverse_proxy backend:8000
    }
    handle /docs {
        reverse_proxy backend:8000
    }
    handle /health {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:3000
    }
}
```

Caddy automatically provisions Let's Encrypt certificates.

### Auto-start on Boot

Docker handles restarts automatically (`restart: unless-stopped`). Ensure Docker starts on boot:

```bash
# Linux
sudo systemctl enable docker

# macOS/Windows - Docker Desktop starts automatically
```

### Backup & Recovery

The backup container creates consistent SQLite snapshots every 10 minutes:

```
./backend/data/          →  ./backend/backups/
├── stocks.db                ├── stocks.db (atomic copy)
└── images/                  └── images/ (rsync)
```

**Pull backups to another machine:**

```bash
rsync -az pi@server:/path/to/backend/backups/ ~/party-backups/
```

**Recovery:**

```bash
cp ~/party-backups/stocks.db ./backend/data/
cp -r ~/party-backups/images/* ./backend/data/images/
docker compose up -d
```

**External backup drive:**

```yaml
# docker-compose.yml
backup:
  volumes:
    - ./backend/data:/data:ro
    - /mnt/usb-backup:/backups  # External drive
```

### Database Migrations

```bash
# In Docker
docker compose exec backend alembic upgrade head

# Local development
cd backend && uv run alembic upgrade head

# Create new migration after model changes
cd backend && uv run alembic revision --autogenerate -m "description"
```

## Configuration

Key environment variables (in `backend/.env`):

| Variable | Description |
|----------|-------------|
| `ATLASCLOUD_API_KEY` | Required for AI content generation |
| `GOOGLE_AI_API_KEY` | Fallback for text generation |
| `CORS_ALLOW_ALL` | Set `true` for development |

See `backend/README.md` for complete configuration reference.

## Project Structure

```
schoen.macht.geld/
├── backend/                 # FastAPI backend
│   ├── src/app/             # Application code
│   ├── data/                # Database + images
│   ├── backups/             # Periodic backups
│   └── scripts/             # Utility scripts
├── frontend/                # Next.js frontend
│   └── src/
│       ├── app/             # Pages (App Router)
│       ├── components/      # React components
│       ├── hooks/           # SWR data fetching
│       └── lib/api/         # Generated API client
├── docker-compose.yml       # Production orchestration
└── Caddyfile                # Reverse proxy config
```

## License

Private project for VAK / Amphitheater events.
