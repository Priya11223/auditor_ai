# Invoice Audit & Validation Platform

A production-style, containerized, agentic Invoice Audit and Validation Platform built with LangGraph, FastAPI, PostgreSQL, Redis, Qdrant, and Streamlit.

## Architecture

| Service | Port | Purpose |
|---------|------|---------|
| `agent-service` | 8000 | Core processing engine (FastAPI) |
| `mock-erp` | 8001 | Mock ERP HTTP API (FastAPI) |
| `streamlit-ui` | 8501 | Human-in-the-loop dashboard |
| `postgres` | 5432 | System of record |
| `redis` | 6379 | Translation cache |
| `qdrant` | 6333 | Vector index for RAG |

## Quick Start

### Prerequisites

- Docker Desktop
- Docker Compose v2+

### Setup

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and start all services
docker compose up --build

# 3. Verify health
curl http://localhost:8000/health/ready
```

### Health Check Endpoints

| Service | Liveness | Readiness |
|---------|----------|-----------|
| Agent Service | `GET :8000/health` | `GET :8000/health/ready` |
| Mock ERP | `GET :8001/health` | `GET :8001/health/ready` |
| Streamlit | `GET :8501/_stcore/health` | — |

### Access Points

- **Streamlit Dashboard**: http://localhost:8501
- **Agent Service API**: http://localhost:8000/docs
- **Mock ERP API**: http://localhost:8001/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Project Structure

```
invoice-auditor/
├── services/
│   ├── agent-service/     # Core processing engine
│   ├── mock-erp/          # Mock ERP HTTP API
│   └── streamlit-ui/      # Human dashboard
├── database/
│   ├── init/              # Schema initialization
│   ├── migrations/        # Alembic migrations
│   └── seeds/             # ERP seed data
├── configs/
│   └── rules.yaml         # Validation & tolerance rules
├── incoming/              # Invoice input folder
├── reports/               # Generated reports
├── docker-compose.yml
└── .env.example
```

## Development Phases

- [x] Phase 0: Architecture & Design
- [ ] Phase 1: Docker Compose + Infrastructure
- [ ] Phase 2: Database Layer
- [ ] Phase 3: Mock ERP Service
- [ ] Phase 4-16: See implementation plan
