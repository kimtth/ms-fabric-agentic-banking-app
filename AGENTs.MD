# Microsoft Fabric OLTP/OLAP Application + Agent + Power BI Demo

## Overview (Refactored)
Refactored and cleaned version of [Agentic Banking App with SQL in Fabric](https://github.com/Azure-Samples/sql-agentic-app-with-fabric) focused on core workload patterns using **Microsoft Fabric SQL**:
- **OLTP** – Fast transactional writes
- **OLAP** – Near-real-time operational insights
- **OLAP** – Historical analytics
- **Agent** – Optional AI-assisted analysis via Azure OpenAI (no Fabric Data Agent)

### What Changed
- Removed LangChain & Flask
- Removed RAG features not needed for OLTP/OLAP
- Removed Fabric Agent (requires commercial capacity licensing)
- Simplified UI, data models, and Fabric artifacts to emphasize OLTP/OLAP

### Architecture
| Layer    | Technology                         | Purpose                          |
|----------|------------------------------------|----------------------------------|
| Frontend | Next.js + React + TypeScript       | Minimal UI with 5 pages          |
| Backend  | FastAPI + Uvicorn + Azure OpenAI   | REST API + optional chat agent   |
| Backend  | SQLAlchemy                         | Fabric SQL ODBC driver           |
| Database | Microsoft Fabric SQL               | Data source                      |

### Data Model
```
users (id, name, email, created_at)
  ↓
accounts (id, user_id, account_number, account_type, balance, name, created_at)
  ↓
transactions (id, from_account_id, to_account_id, amount, type, description, category, status, created_at)

chat_sessions (session_id, user_id, title, created_at, updated_at)
  ↓
chat_history (message_id, session_id, trace_id, user_id, message_type, content, ...)
```

## Workload Patterns
### 1. OLTP
Purpose: Fast, atomic writes (ACID). Endpoints: `POST /oltp/users`, `POST /oltp/accounts`, `POST /oltp/transfer`

### 2. OLAP
Purpose: Near-real-time operational insights. Endpoints: `GET /oltap/summary`, `GET /oltap/dashboard`

### 3. OLAP
Purpose: Historical analytics. Endpoints: `GET /olap/spend`, `GET /olap/analytics`, `GET /olap/category-trends`

### 4. Agent (Optional)
Purpose: Natural language queries assisted by Azure OpenAI.
Features:
- Read-only SQL function tool (SELECT only)
- Session management
- Not using Fabric Data Agent
Endpoints: `POST /agent/chat`, `GET /agent/sessions`, `GET /agent/history/{session_id}`

## API Contracts
- Health: `GET /health`
- OLTP: `GET|POST /oltp/{users,accounts}`, `POST /oltp/transfer`
- OLAP: `GET /oltap/{summary,dashboard}?windowMinutes=60`
- OLAP: `GET /olap/{spend,analytics,category-trends}?from=DATE&to=DATE`
- Agent: `POST /agent/chat`, `GET /agent/sessions?user_id=X`, `GET /agent/history/{session_id}`

## Backend Files
- `app/db.py` – Database connection helpers
- `app/main.py` – FastAPI endpoints
- `app/agent.py` – Azure OpenAI agent with tool calling

## Accessing Fabric SQL
See [backend/.env.sample](backend/.env.sample) for connection guidance:
- Use ODBC Driver 18
- Local dev: `Authentication=ActiveDirectoryInteractive`
- Automation: service principal recommended; grant roles in Fabric SQL; enable tenant setting “Service principals can use Fabric APIs”
- Set `FRONTEND_ORIGIN` for CORS

## Running the Application
### Backend
```bash
cd backend
uv sync
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Data Setup
Sample data and views:
- Banking sample data: [backend/demo_data.py](backend/demo_data.py)
- Chat history sample data: [backend/demo_chat_data.py](backend/demo_chat_data.py)
- Reporting views: [backend/create_view.sql](backend/create_view.sql)

## Changes
Removed:
- Flask → FastAPI
- LangChain/LangGraph → Microsoft Agent Framework
- RAG/Vector search → Removed
- Fabric Data Agent → Removed

Retained:
- OLTP/OLAP patterns
- Agent with database query tool
- Chat history persistence
- SQLAlchemy

## Products
- Power BI report: [fabric_asset/artifacts/Agent_Insights.Report](fabric_asset/artifacts/Agent_Insights.Report)
- Semantic model: [fabric_asset/artifacts/agentic_semantic_model.SemanticModel](fabric_asset/artifacts/agentic_semantic_model.SemanticModel)
- Demo application: this repository (frontend + backend)

## References
- [Microsoft Fabric SQL](https://learn.microsoft.com/en-us/fabric/data-warehouse/sql-endpoints)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Azure OpenAI](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
