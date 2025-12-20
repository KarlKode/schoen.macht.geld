# System Architecture

**Project**: Schön. Macht. Geld. - Stock Exchange Party Game
**Event**: One-time party event with ~1000 guests
**Organizers**: VAK (Verein für ambitionierten Konsum) & Amphitheater Zürich

---

## Overview

A satirical stock exchange game where party guests become tradeable "stocks". Guests can interact with the market through swipe-based games, affecting stock prices in real-time. Multiple display screens show live market visualizations.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CENTRAL SERVER (Pi 4 / Laptop)                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Docker Compose Stack (root level)               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌───────┐  ┌────────┐         │   │
│  │  │ Frontend │  │ Backend  │  │ Caddy │  │ Backup │         │   │
│  │  │ Next.js  │  │ FastAPI  │  │ Proxy │  │ SQLite │         │   │
│  │  │  :3000   │  │  :8000   │  │ :80   │  │ Cron   │         │   │
│  │  └────┬─────┘  └────┬─────┘  └───┬───┘  └────────┘         │   │
│  │       └─────────────┴────────────┘                          │   │
│  │                      ↑ internal network                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                         port 80 (HTTP)                              │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
              Private WiFi Network (no guest access)
         ┌─────────────┬───────┴───────┬─────────────┐
         │             │               │             │
    ┌────┴────┐   ┌────┴────┐    ┌─────┴────┐  ┌─────┴────┐
    │ Pi Zero │   │ Pi Zero │    │   Pi 4   │  │   Pi 4   │
    │ Display │   │ Display │    │  Swipe   │  │  Admin   │
    │ /ticker │   │ /leader │    │ /swipe   │  │ /admin   │
    │  board  │   │  board  │    │          │  │          │
    └─────────┘   └─────────┘    └──────────┘  └──────────┘
      Chromium      Chromium       Chromium     Chromium
      Kiosk Mode    Kiosk Mode     Kiosk Mode   Kiosk Mode
```

---

## Components

### 1. Backend (FastAPI + SQLite)

**Location**: `/backend/`

**Responsibilities**:
- Stock CRUD operations
- Swipe processing with price calculations
- Price snapshots and ranking calculations (scheduled)
- AI generation (descriptions, images, videos)
- Admin interface (`/admin`)

**Stack**:
- Python 3.13 + FastAPI
- SQLModel + SQLite (async via aiosqlite)
- Alembic for migrations
- APScheduler for background jobs
- sqladmin for admin UI

**Key Endpoints**:
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/stocks/` | List all stocks |
| POST | `/stocks/` | Create stock |
| GET | `/stocks/{ticker}` | Get single stock |
| POST | `/stocks/{ticker}/image` | Upload image |
| POST | `/stocks/{ticker}/price` | Admin price adjustment |
| GET | `/stocks/{ticker}/snapshots` | Price history for charts |
| POST | `/swipe/` | Record swipe (up/down) |
| GET | `/health` | Health check |
| POST | `/ai/generate/*` | AI generation endpoints |

### 2. Frontend (Next.js)

**Location**: `/frontend/` (after reorganization)

**Pages**:
| Route | Purpose | Target Device |
|-------|---------|---------------|
| `/display` | Scrolling stock ticker | Pi Zero |
| `/display/leaderboard` | Stock grid sorted alphabetically | Pi Zero |
| `/display/market-map` | Treemap visualization | Pi Zero |
| `/display/stock-chart` | Rotating price charts | Pi Zero |
| `/display/terminal` | Bloomberg-style terminal with AI news | Pi Zero |
| `/swipe` | Tinder-like swipe interface | Pi 4 |

**Stack**:
- Next.js 15 (React 19)
- SWR for data fetching with polling
- Tailwind CSS + Radix UI
- Recharts for visualizations
- Framer Motion for animations

### 3. Caddy (Reverse Proxy)

**Purpose**: Single entry point, routes requests to appropriate service

**Routing**:
```
:80
├── /api/*     → backend:8000  (API requests)
├── /admin/*   → backend:8000  (Admin UI)
├── /images/*  → file server   (Static images)
└── /*         → frontend:3000 (Next.js app)
```

### 4. Backup Service

**Purpose**: Automated SQLite snapshots + image backups

**Schedule**: Every 10 minutes

**Storage**: `./backend/backups/` with timestamped snapshots

---

## Data Flow

### Stock Display (Read Path)
```
Pi Browser → Caddy → Frontend (SSR or client) → Backend API → SQLite
                                    ↓
                              SWR Cache (2s TTL)
                                    ↓
                              React Components
```

### Swipe Action (Write Path)
```
Pi Browser (swipe gesture)
       ↓
Frontend: POST /api/swipe { ticker, direction, token }
       ↓
Backend: Validate token, calculate price delta
       ↓
SQLite: Create PriceEvent, update Stock.current_price
       ↓
Response: { new_price, new_token }
       ↓
Frontend: Update UI optimistically + refetch
```

### Price Updates (Background)
```
APScheduler (every 30s)
       ↓
Create StockSnapshot for each stock
       ↓
Calculate rankings
       ↓
Update Stock.rank fields
```

---

## Network Topology

### Hardware
| Device | Role | Connection | Browser Route |
|--------|------|------------|---------------|
| Central Server | Docker host | Wired LAN | - |
| Pi Zero 2W #1 | Ticker display | WiFi | `http://server/display` |
| Pi Zero 2W #2 | Leaderboard | WiFi | `http://server/display/leaderboard` |
| Pi Zero 2W #3 | Market map | WiFi | `http://server/display/market-map` |
| Pi Zero 2W #4 | Stock chart | WiFi | `http://server/display/stock-chart` |
| Pi Zero 2W #5 | Terminal | WiFi | `http://server/display/terminal` |
| Pi 4 #1 | Swipe kiosk | WiFi/Wired | `http://server/swipe` |
| Pi 4 #2 | Admin/Backup | Wired | `http://server/admin` |

### Network Requirements
- Private WiFi network (not accessible to guests)
- Static IP for central server (e.g., `192.168.1.100`)
- All Pis configured to auto-start Chromium in kiosk mode

### Resilience
- Frontend uses SWR with `fallbackData` for graceful degradation
- If API unreachable, displays continue showing last known data
- Swipe kiosks show error toast but don't crash

---

## Deployment

### Central Server Setup
```bash
# Clone and navigate
cd /path/to/schoen.macht.geld

# Start all services
docker compose up -d

# Check health
curl http://localhost/health
```

### Pi Kiosk Setup
```bash
# /etc/xdg/lxsession/LXDE-pi/autostart (example)
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk --noerrdialogs --disable-infobars \
  http://192.168.1.100/display/leaderboard
```

---

## Environment Variables

### Backend (`backend/.env`)
```env
DATABASE_URL=sqlite+aiosqlite:///./data/stocks.db
IMAGE_DIR=/app/data/images

# AI Configuration
GEMINI_API_KEY=...
ATLASCLOUD_API_KEY=...
ATLASCLOUD_TEXT_MODEL=...
ATLASCLOUD_IMAGE_MODEL=...
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://backend:8000
```

---

## Security Considerations

- Network is private (no guest access)
- No authentication required for kiosk operations
- Admin panel accessible only from trusted devices
- SQLite database backed up every 10 minutes
- No sensitive data stored (it's a party game)
