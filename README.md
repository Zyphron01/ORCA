# ORCA Marine Intelligence Platform

> **Team Bytecrats** | SIH 2026 | Problem Statement ID: **SIH26176**  
> Theme: Space Technology | Category: Software

---

## What is ORCA?

**ORCA** (Ocean Reasoning and Collaborative Agents) is the AI brain of the ORCA platform — an Agentic Marine Intelligence System designed for Indian fishermen and the Indian Coast Guard.

ORCA understands natural language (including Indian regional languages), plans multi-step marine intelligence tasks, delegates to specialized agents (weather, ocean, SAR, hazard), and synthesizes evidence into actionable rescue plans, safety alerts, and live maps.

---

## Quick Start (Phase 0)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker + Docker Compose
- Git

### 1. Clone and configure
```powershell
git clone <repo-url>
cd ORCA
Copy-Item .env.example .env
# Edit .env and fill in your LLM_API_KEY
```

### 2. Start everything with one command
```powershell
.\scripts\dev.ps1
```

This will:
1. Install Python dependencies
2. Install Node.js dependencies
3. Start PostgreSQL + PostGIS + Redis via Docker
4. Run Alembic migrations
5. Seed demo data
6. Start FastAPI on http://localhost:8000
7. Start React dev server on http://localhost:5173

### 3. Verify
- API health: http://localhost:8000/api/v1/health
- API docs: http://localhost:8000/docs
- Coast Guard Console: http://localhost:5173

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│              ORCA Platform                      │
│                                                              │
│  ┌─────────────┐   ┌─────────────────────────────────────┐  │
│  │ Mobile Edge │   │         Cloud Brain (ORCA)           │  │
│  │ (Android)   │   │  ┌────────────────────────────────┐ │  │
│  │             │   │  │  ORCA Supervisor (ReAct/LangGraph│ │  │
│  │ Offline STT │   │  │  Multi-turn | Planning | Evidence│ │  │
│  │ H3 Cache    │◄──┤  └───────────┬────────────────────┘ │  │
│  │ BLE Bridge  │   │              │ delegates             │  │
│  │ Capsize Det │   │  ┌───────────┼──────────────────┐   │  │
│  └─────────────┘   │  │           │                  │   │  │
│                    │  ▼           ▼          ▼       ▼   │  │
│  ┌─────────────┐   │ Hydro  Marine EO  Hazard    SAR     │  │
│  │ Coast Guard │   │ Meteo  Agent      Sentry   Physics  │  │
│  │   Console   │   │ Agent  (Bhoon.)   (IMBL)   (RK4)   │  │
│  │  (React.js) │   │                                     │  │
│  │  MapLibre   │   │  ┌──────────────────────────────┐  │  │
│  │  Deck.gl    │◄──┤  │   Tactical Comms Agent        │  │  │
│  │  WebSocket  │   │  │   CAP XML | P2P Fleet | NavIC  │  │  │
│  └─────────────┘   │  └──────────────────────────────┘  │  │
└──────────────────────────────────────────────────────────────┘
```

---

## Endpoints & URLs

- **API Base URL**: `https://orca-1jo3.onrender.com`
- **Frontend App**: (Deployed on Vercel)
- **API Documentation**: `https://orca-1jo3.onrender.com/docs`
- **Mobile APK**: Accessible via EAS (Expo Application Services)

---

## Build Phases

| Phase | Status | Description |
|---|---|---|
| 0-16 | 🟢 Completed | Core infrastructure, agentic reasoning, SAR physics, geospatial mapping, and Coast Guard console |
| 17 | 🟢 Completed | Production deployment to Render, Vercel, and EAS |

---

## Important Notes

- All external data (INCOIS, IMD, Bhoonidhi, ISRO transponders) uses **mock adapters** until real credentials are provided.
- All simulated data is clearly labelled `"source": "MOCK-*"` in API responses.
- No real government data is fabricated. Mock data is synthetic and clearly distinguished.
- Real adapter interfaces are defined — swap mock → real without changing ORCA logic.

---

## Project Structure

```
ORCA/
├── apps/api/          # FastAPI backend
├── apps/web/          # React Coast Guard Console
├── packages/          # Shared libraries
│   ├── shared-types/  # Pydantic + TypeScript models
│   ├── orca-core/     # ORCA supervisor engine
│   ├── orca-agents/   # Specialized agents
│   ├── orca-tools/    # LangGraph tools
│   ├── marine-data/   # Data adapters
│   ├── sar-physics/   # RK4 drift engine
│   ├── geospatial/    # H3 + PostGIS utilities
│   └── comms/         # BLE/satellite abstractions
├── infra/             # Docker Compose, DB init
├── data/              # Mock data, fixtures, schemas
├── docs/              # Architecture documentation
└── scripts/           # Dev tooling
```

---

## License & Credits

Team Bytecrats | SIH 2026 | ORCA ORCA Marine Platform
