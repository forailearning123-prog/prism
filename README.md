# Project Prism

An AI-Native Business Decision Intelligence Platform.

Prism is not another BI tool, not Power BI with AI, and not another dashboard product.
Prism is an **AI Operating System for Business Decisions**.

## Core Problem

Companies already have data, but business decisions are trapped inside people and slow handoffs.
A typical chain looks like:

- CEO asks Finance
- Finance asks BI team
- BI team asks Data Engineer
- Data Engineer asks DBA

By the time a dashboard arrives, the key question remains: **"So what should we do?"**

Prism acts as a digital executive team that continuously watches the business and recommends actions.

## What Prism Delivers

Instead of users pulling reports, Prism pushes intelligence such as:

- Inventory shortage likely next Tuesday
- Cash flow risk in 18 days
- Three customers likely to churn
- Hiring can be delayed by two months
- Marketing spend on Meta is underperforming

Prism sells **business decisions**—not dashboards, reports, or KPIs.

## Executive AI Counterparts

Every company gets AI executives available 24x7:

- AI CFO: financial health, cash flow, forecasts, profitability, cost optimization, investment suggestions
- AI COO: operations, supply chain, manufacturing, inventory, vendor performance
- AI Sales Director: pipeline, forecast, lead scoring, sales performance, territory optimization
- AI HR Director: hiring, attrition, performance, compensation, retention
- AI Marketing Director: campaign ROI, acquisition, retention, optimization
- AI CEO Assistant: daily summary, critical risks, top opportunities, priorities, decision tracking

## Example Decision Output

A morning briefing can proactively provide:

- Revenue decreased 8%
- Primary reason: North India sales dropped due to reduced distributor ordering frequency
- Expected impact: ₹1.8 crore (18 million rupees) revenue reduction over next 45 days
- Recommendation: Offer Distributor Incentive Plan A
- Probability of recovery: 81%

## Editions

Prism is offered in three editions:

1. **Community Edition** - Free, self-hosted/local for developers and small teams
2. **Professional Edition** - Subscription for SMEs in India, ranging from ₹2,500-₹5,000/month depending on plan tier and feature requirements
3. **Enterprise Edition** - Custom pricing with SSO, RBAC, audit, advanced governance, and deployment on customer infrastructure

Professional pricing is presented in INR for India; equivalent pricing is localized by market.

## Deployment & Architecture

- Separate frontend (FE) and backend (BE) services
- Deployment on KVM using Coolify
- Deployment flexibility across SaaS, Azure, AWS, GCP, on-premises, or customer-managed cloud infrastructure

This deployment flexibility is a key competitive differentiator for Prism.

---

## Getting Started

### Local Development (Docker)

**Prerequisites:** Docker and Docker Compose installed.

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env — set a strong SECRET_KEY

# 2. Start everything
docker compose up --build

# Frontend: http://localhost
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Demo credentials:** `demo@prism.ai` / `demo1234`

### Local Dev (without Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:5173  (proxies /api/* to backend)
```

### Deploying on KVM with Coolify

1. **Add your KVM server** to Coolify as a remote server (SSH key auth).
2. **Create a new Docker Compose resource** pointing to this repository.
3. **Set environment variables** in Coolify:
   - `SECRET_KEY` — generate with `openssl rand -hex 32`
   - `FRONTEND_URL` — your public domain (e.g. `https://prism.example.com`)
4. **Configure a domain** in Coolify and enable HTTPS (Let's Encrypt).
5. **Deploy** — Coolify builds and starts both services.

The nginx frontend container proxies `/api/*` to the backend, so no CORS issues in production.

## Project Structure

```
prism/
├── backend/               FastAPI (Python)
│   ├── app/
│   │   ├── main.py        App entry point, lifespan, CORS
│   │   ├── config.py      Settings & environment
│   │   ├── auth.py        JWT authentication helpers
│   │   ├── models.py      SQLAlchemy ORM models
│   │   ├── schemas.py     Pydantic request/response schemas
│   │   ├── database.py    Async SQLite setup
│   │   └── routers/       API route handlers
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/              React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── App.jsx        Router and route definitions
│   │   ├── components/    Layout, Sidebar, Header, Cards
│   │   ├── pages/         Dashboard, Briefing, Executives, Settings
│   │   ├── context/       AuthContext (JWT + user state)
│   │   └── services/      Axios API client
│   ├── nginx.conf         SPA + API proxy config
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/token` | Login — returns JWT |
| GET | `/api/v1/auth/me` | Current user profile |
| GET | `/api/v1/executives` | List AI executives |
| GET | `/api/v1/executives/{id}` | Get one AI executive |
| GET | `/api/v1/briefing/daily` | Daily intelligence briefing |
| GET | `/api/v1/briefing/insights` | All active insights |

Interactive docs available at `/docs` (Swagger UI) when the backend is running.
