# Migration & Reorganization Plan

This document outlines the steps to migrate from Firebase to the new backend and reorganize the project structure.

---

## Phase 1: Project Reorganization

### Current Structure
```
/schoen.macht.geld
├── backend/           # FastAPI backend
│   ├── docker-compose.yml
│   ├── Caddyfile
│   └── ...
├── src/               # Next.js frontend source
├── node_modules/
├── package.json
├── next.config.ts
├── firestore.rules    # DELETE
├── apphosting.yaml    # DELETE (Firebase hosting)
└── ...config files
```

### Target Structure
```
/schoen.macht.geld
├── docker-compose.yml          # Root orchestration (moved from backend/)
├── Caddyfile                   # Reverse proxy config (moved from backend/)
├── .gitignore                  # OS/IDE ignores only
├── backend/
│   ├── .gitignore              # Backend-specific ignores
│   ├── Dockerfile
│   ├── src/app/
│   ├── data/                   # SQLite + images (ignored)
│   └── backups/                # Backup snapshots (ignored)
├── frontend/
│   ├── .gitignore              # Frontend-specific ignores
│   ├── Dockerfile              # NEW
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/              # NEW: Custom hooks
│   │   └── lib/
│   │       └── api/            # NEW: Generated API client
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AI_PROMPTS.md
│   └── MIGRATION_PLAN.md
├── scripts/
│   └── setup-pi.sh
└── README.md
```

### Step 1.1: Create Frontend Directory & Move Files

```bash
# Create frontend directory
mkdir -p frontend

# Move Next.js files
mv src frontend/
mv public frontend/ 2>/dev/null || true
mv package.json frontend/
mv package-lock.json frontend/ 2>/dev/null || true
mv pnpm-lock.yaml frontend/ 2>/dev/null || true
mv next.config.ts frontend/
mv next-env.d.ts frontend/
mv tsconfig.json frontend/
mv tailwind.config.ts frontend/
mv postcss.config.mjs frontend/
mv components.json frontend/

# Remove Firebase-specific files
rm -f firestore.rules
rm -f apphosting.yaml
rm -rf .idx

# Clean up (reinstall later)
rm -rf node_modules
rm -rf .next

# Create new directories
mkdir -p frontend/src/lib/api
mkdir -p frontend/src/hooks
```

### Step 1.2: Move Docker/Caddy to Root

```bash
# Move orchestration files to root
mv backend/docker-compose.yml ./
mv backend/Caddyfile ./

# Keep backup service config in backend (it's backend-specific)
# The backup/ directory stays in backend/
```

### Step 1.3: Setup Gitignore Files

**Root `.gitignore`** (OS/IDE only):
```gitignore
# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
*.swo

# Local storage (development artifacts)
.localstorage*
```

**`frontend/.gitignore`**:
```gitignore
# Dependencies
node_modules/

# Next.js
.next/
out/

# Environment
.env
.env.local
.env.*.local

# Generated API client
src/lib/api/client/

# Misc
*.tsbuildinfo
next-env.d.ts
```

**`backend/.gitignore`** (already exists, verify it has):
```gitignore
# Python
.venv/
__pycache__/
*.pyc

# Data (persisted but not tracked)
data/
backups/

# Environment
.env
```

---

## Phase 2: Remove Firebase Dependencies

### Step 2.1: Files to Delete

```
frontend/src/firebase/           # Entire directory
├── config.ts
├── index.ts
├── provider.tsx
├── client-provider.tsx
├── errors.ts
├── error-emitter.ts
├── non-blocking-login.tsx
├── non-blocking-updates.tsx
└── firestore/
    ├── use-collection.tsx
    └── use-doc.tsx

frontend/src/ai/                 # Entire directory (consolidate to backend)
├── genkit.ts
└── flows/
    ├── generate-profile-descriptions.ts
    └── generate-funny-news-headlines.ts

frontend/src/components/
└── FirebaseErrorListener.tsx    # Delete
```

### Step 2.2: Dependencies to Remove

Remove from `frontend/package.json`:
```json
{
  "dependencies": {
    "firebase": "...",
    "@genkit-ai/google-genai": "...",
    "genkit": "..."
  }
}
```

### Step 2.3: Dependencies to Add

```bash
cd frontend
pnpm add swr
pnpm add -D @hey-api/openapi-ts
```

---

## Phase 3: Generate TypeScript API Client

Using `@hey-api/openapi-ts` for type-safe API client generation.

### Step 3.1: Add Generation Script

Add to `frontend/package.json`:
```json
{
  "scripts": {
    "generate-api": "npx @hey-api/openapi-ts -i http://localhost:8000/openapi.json -o src/lib/api/client -c @hey-api/client-fetch"
  }
}
```

### Step 3.2: Generate Client

```bash
# Start backend
docker compose up backend -d

# Generate TypeScript client from OpenAPI
cd frontend
pnpm generate-api
```

This creates `src/lib/api/client/` with:
- `types.gen.ts` - All TypeScript types from the OpenAPI schema
- `sdk.gen.ts` - Generated SDK functions for each endpoint
- `client.gen.ts` - HTTP client configuration

### Step 3.3: Usage Examples

The generated client provides typed functions:

```typescript
import { client } from '@/lib/api/client/client.gen';
import { listStocks, getStock, getStockSnapshots, submitSwipe } from '@/lib/api/client/sdk.gen';

// Configure base URL
client.setConfig({ baseUrl: '/api' });

// List all stocks
const { data: stocks } = await listStocks();

// Get single stock
const { data: stock } = await getStock({ path: { ticker: 'ABC' } });

// Get snapshots for charts
const { data: snapshots } = await getStockSnapshots({ path: { ticker: 'ABC' }, query: { limit: 100 } });

// Submit swipe
const { data: result } = await submitSwipe({
  body: { ticker: 'ABC', direction: 'up', token: previousToken }
});
```

### Step 3.4: SWR Hooks (`frontend/src/hooks/use-stocks.ts`)

```typescript
import useSWR from 'swr';
import { listStocks, getStock, getStockSnapshots } from '@/lib/api/client/sdk.gen';
import type { StockResponse } from '@/lib/api/client/types.gen';

// Fallback data for resilience
const FALLBACK_STOCKS: StockResponse[] = [
  // Add 3-5 dummy stocks for graceful degradation
];

export function useStocks() {
  const { data, error, isLoading, mutate } = useSWR(
    'stocks',
    async () => {
      const { data } = await listStocks();
      return data;
    },
    {
      fallbackData: FALLBACK_STOCKS,
      refreshInterval: 2000,
      revalidateOnFocus: false,
      dedupingInterval: 1000,
    }
  );

  return {
    stocks: data ?? FALLBACK_STOCKS,
    isLoading,
    isError: !!error,
    mutate,
  };
}

export function useStock(ticker: string) {
  return useSWR(
    ticker ? `stock-${ticker}` : null,
    async () => {
      const { data } = await getStock({ path: { ticker } });
      return data;
    },
    {
      refreshInterval: 2000,
      revalidateOnFocus: false,
    }
  );
}

export function useStockSnapshots(ticker: string, limit = 100) {
  return useSWR(
    ticker ? `snapshots-${ticker}` : null,
    async () => {
      const { data } = await getStockSnapshots({ path: { ticker }, query: { limit } });
      return data;
    },
    {
      refreshInterval: 5000,
      revalidateOnFocus: false,
    }
  );
}
```

### Advantages of @hey-api/openapi-ts

1. **Type-safe**: All request/response types match backend exactly
2. **Auto-updated**: Re-run `pnpm generate-api` when backend changes
3. **Modern API**: Clean function-based SDK with proper TypeScript inference
4. **IDE support**: Full autocomplete for all endpoints and parameters
5. **FastAPI recommended**: Official approach from FastAPI docs

---

## Phase 4: Migrate Components

### Components to Migrate

| Component | Location | Changes Required |
|-----------|----------|------------------|
| `leaderboard-client.tsx` | `/display/leaderboard/` | Replace `useCollection` → `useStocks` |
| `market-map-client.tsx` | `/display/market-map/` | Replace `useCollection` → `useStocks` |
| `stock-chart-client.tsx` | `/display/stock-chart/` | Replace `useCollection` → `useStocks` + `useStockSnapshots` |
| `terminal-client.tsx` | `/display/terminal/` | Replace `useCollection` → `useStocks`, AI → backend |
| `swipe-client.tsx` | `/swipe/` | Replace Firestore transaction → `submitSwipe()` |
| `layout.tsx` | `/app/` | Remove `FirebaseProvider`, add `SWRConfig` |

### Components to Delete

| Component | Reason |
|-----------|--------|
| `/register/` | Use backend admin instead |
| `edit-stock-dialog.tsx` | Part of registration |
| `registration-client.tsx` | Part of registration |
| `FirebaseErrorListener.tsx` | Firebase-specific |

### Step 4.1: Update Root Layout

**Before** (`frontend/src/app/layout.tsx`):
```tsx
import { FirebaseClientProvider } from '@/firebase/client-provider';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <FirebaseClientProvider>
          {children}
        </FirebaseClientProvider>
      </body>
    </html>
  );
}
```

**After**:
```tsx
import { SWRConfig } from 'swr';

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <SWRConfig value={{
          revalidateOnFocus: false,
          dedupingInterval: 1000,
        }}>
          {children}
        </SWRConfig>
      </body>
    </html>
  );
}
```

### Step 4.2: Example Component Migration

**Before** (`leaderboard-client.tsx`):
```tsx
import { useFirebase } from '@/firebase/provider';
import { useCollection } from '@/firebase/firestore/use-collection';
import { collection } from 'firebase/firestore';

export function LeaderboardClient() {
  const { firestore } = useFirebase();
  const titlesCollection = useMemoFirebase(
    () => collection(firestore, 'titles'),
    [firestore]
  );
  const { data: stocks, isLoading } = useCollection<Stock>(titlesCollection);
  // ...
}
```

**After**:
```tsx
import { useStocks } from '@/hooks/use-stocks';

export function LeaderboardClient() {
  const { stocks, isLoading } = useStocks();
  // ... rest unchanged (data shape may need minor adjustments)
}
```

### Step 4.3: Swipe Migration

**Before** (uses Firestore transactions):
```tsx
const handleSwipe = async (direction: 'up' | 'down') => {
  await runTransaction(firestore, async (transaction) => {
    // ... complex transaction logic
  });
};
```

**After**:
```tsx
import { submitSwipe } from '@/lib/api/client/sdk.gen';

const [swipeToken, setSwipeToken] = useState<string>();

const handleSwipe = async (direction: 'up' | 'down') => {
  try {
    const { data: result } = await submitSwipe({
      body: {
        ticker: currentStock.ticker,
        direction,
        token: swipeToken,
      },
    });
    setSwipeToken(result?.token);
    // Trigger refetch of stocks
  } catch (error) {
    console.error('Swipe failed:', error);
  }
};
```

### Step 4.4: Data Model Mapping

The frontend `Stock` type will need slight adjustments to match backend:

| Frontend (Firebase) | Backend (API) |
|---------------------|---------------|
| `id` | `ticker` |
| `nickname` | `title` |
| `photoUrl` | `image` (URL, not data URI) |
| `currentValue` | `current_price` |
| `initialValue` | `reference_price` |
| `percentChange` | Calculated: `(current_price - reference_price) / reference_price * 100` |
| `history[]` | Use `GET /stocks/{ticker}/snapshots` |
| `rank` | `rank` |

---

## Phase 5: Backend Additions

### Required New Endpoints

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `DELETE /stocks/{ticker}` | Admin delete stock | Low (use admin UI) |
| `PUT /stocks/{ticker}` | Full stock update | Low (use admin UI) |
| `POST /ai/generate/headlines` | Generate news headlines | Medium |

### Update AI Prompts

Replace the English description prompt in `backend/src/app/routers/ai.py` with the German party-themed version from `docs/AI_PROMPTS.md`.

---

## Phase 6: Docker Orchestration

### Root `docker-compose.yml`

```yaml
services:
  backend:
    build: ./backend
    restart: unless-stopped
    volumes:
      - ./backend/data:/app/data
      - ./backend/.env:/app/.env:ro
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/stocks.db
      - IMAGE_DIR=/app/data/images
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  frontend:
    build: ./frontend
    restart: unless-stopped
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      backend:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - ./backend/data/images:/srv/images:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      frontend:
        condition: service_healthy

  backup:
    build: ./backend/backup
    volumes:
      - ./backend/data:/data:ro
      - ./backend/backups:/backups
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

### Root `Caddyfile`

```caddyfile
:80 {
    # Serve static images
    handle /images/* {
        root * /srv
        file_server
    }

    # API requests to backend
    handle /api/* {
        uri strip_prefix /api
        reverse_proxy backend:8000
    }

    # Admin panel
    handle /admin/* {
        reverse_proxy backend:8000
    }

    # Health check (backend)
    handle /health {
        reverse_proxy backend:8000
    }

    # Everything else to frontend
    handle {
        reverse_proxy frontend:3000
    }
}
```

### Create `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

# Build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN corepack enable pnpm && pnpm build

# Production
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
```

### Update `frontend/next.config.ts`

Enable standalone output for Docker:
```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',
  // ... other config
};

export default nextConfig;
```

---

## Phase 7: Testing & Deployment

### Local Development

```bash
# Terminal 1: Backend only
docker compose up backend -d

# Terminal 2: Frontend (dev mode with hot reload)
cd frontend
pnpm install
pnpm generate-api  # Generate client from backend
pnpm dev

# Open http://localhost:3000/display/leaderboard
```

### Full Stack (Docker)

```bash
# From project root
docker compose up --build

# Test
curl http://localhost/health
curl http://localhost/api/stocks/
# Open http://localhost/display/leaderboard
```

### Regenerating API Client

Whenever backend API changes:
```bash
cd frontend
pnpm generate-api
# Client is updated, TypeScript will catch any breaking changes
```

---

## Checklist

### Phase 1: Reorganization
- [ ] Create `frontend/` directory
- [ ] Move all Next.js files to `frontend/`
- [ ] Move `docker-compose.yml` and `Caddyfile` to root
- [ ] Delete Firebase config files (`firestore.rules`, `apphosting.yaml`, `.idx/`)
- [ ] Create per-directory `.gitignore` files (root, frontend, backend)

### Phase 2: Remove Firebase
- [ ] Delete `src/firebase/` directory
- [ ] Delete `src/ai/` directory
- [ ] Delete `FirebaseErrorListener.tsx`
- [ ] Remove Firebase/Genkit dependencies from package.json
- [ ] Add SWR and @hey-api/openapi-ts dependencies

### Phase 3: API Client
- [ ] Add `generate-api` script to package.json
- [ ] Generate client: `pnpm generate-api`
- [ ] Create `hooks/use-stocks.ts`

### Phase 4: Component Migration
- [ ] Update root layout (remove Firebase, add SWR)
- [ ] Migrate `leaderboard-client.tsx`
- [ ] Migrate `market-map-client.tsx`
- [ ] Migrate `stock-chart-client.tsx`
- [ ] Migrate `terminal-client.tsx`
- [ ] Migrate `swipe-client.tsx`
- [ ] Delete `/register/` directory
- [ ] Adjust data model mappings (id→ticker, nickname→title, etc.)

### Phase 5: Backend
- [ ] Update AI prompts to German versions

### Phase 6: Docker
- [ ] Update root `docker-compose.yml` with correct paths
- [ ] Update root `Caddyfile`
- [ ] Add `output: 'standalone'` to `frontend/next.config.ts`
- [ ] Create `frontend/Dockerfile`
- [ ] Test full stack locally

### Phase 7: Deployment
- [ ] Deploy to central server
- [ ] Configure Pi kiosks
- [ ] End-to-end testing
