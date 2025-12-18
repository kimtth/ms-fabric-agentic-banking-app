import os
import uuid
import uvicorn
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from dotenv import load_dotenv
from pathlib import Path

# Load environment variables early so imports relying on them succeed
load_dotenv()  # Load from current working directory
load_dotenv(Path(__file__).with_name(".env"))  # Also load backend/.env if present

from app.db import get_session  # noqa: E402
from app import agent, sql  # noqa: E402


def _iso_or_none(v: Optional[str]) -> Optional[str]:
    """Convert ISO string or None."""
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00")).isoformat()
    except Exception:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize agent client (optional - will fail gracefully if Azure OpenAI not configured)
    try:
        agent.init_agent()
        print("✓ Agent initialized successfully")
    except Exception as e:
        print(f"⚠ Warning: Agent initialization failed: {e}")
        print("  Server will continue without agent functionality")
    yield
    # Shutdown: add cleanup here if needed


app = FastAPI(title="Fabric OLTP/OLTAP/OLAP + Agent API", lifespan=lifespan)

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if env_origin := os.getenv("FRONTEND_ORIGIN"):
    origins.append(env_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/health")
def health():
    return {"ok": True}


@app.get("/oltp/users")
def list_users():
    with get_session() as session:
        rows = session.execute(text(sql.LIST_USERS)).fetchall()
        return [dict(r._mapping) for r in rows]


@app.post("/oltp/users")
def create_user(payload: dict):
    with get_session() as session:
        session.execute(text(sql.CREATE_USER), {
            "id": payload.get("id"),
            "name": payload.get("name"),
            "email": payload.get("email")
        })


@app.get("/oltp/accounts")
def list_accounts():
    with get_session() as session:
        rows = session.execute(text(sql.LIST_ACCOUNTS)).fetchall()
        return [dict(r._mapping) for r in rows]


@app.post("/oltp/accounts")
def create_account(payload: dict):
    with get_session() as session:
        session.execute(text(sql.CREATE_ACCOUNT), {
            "id": payload.get("id"),
            "user_id": payload.get("userId"),
            "account_number": payload.get("accountNumber"),
            "account_type": payload.get("accountType"),
            "balance": payload.get("balance"),
            "name": payload.get("name")
        })
    return {"ok": True}


@app.post("/oltp/transfer")
def transfer(payload: dict):
    tx_id = f"t_{uuid.uuid4().hex[:12]}"
    amount = payload.get("amount")
    from_id = payload.get("fromAccountId")
    to_id = payload.get("toAccountId")
    description = payload.get("description")
    category = payload.get("category") or "Transfer"

    with get_session() as session:
        session.execute(text(sql.TRANSFER_DEBIT), {"amount": amount, "id": from_id})
        session.execute(text(sql.TRANSFER_CREDIT), {"amount": amount, "id": to_id})
        session.execute(text(sql.INSERT_TRANSACTION), {
            "id": tx_id,
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": amount,
            "type": "transfer",
            "description": description,
            "category": category,
            "status": "posted"
        })

    return {"ok": True, "transactionId": tx_id}


@app.get("/oltap/summary")
def oltap_summary(windowMinutes: int = 60):
    with get_session() as session:
        base = session.execute(text(sql.OLTAP_SUMMARY), {"window_minutes": windowMinutes}).fetchone()
        cats = session.execute(text(sql.OLTAP_TOP_CATEGORIES), {"window_minutes": windowMinutes}).fetchall()

    return {
        "windowMinutes": windowMinutes,
        "transactions": base.transactions if base else 0,
        "totalAmount": base.totalAmount if base else 0,
        "topCategories": [dict(r._mapping) for r in cats],
    }


@app.get("/oltap/dashboard")
def oltap_dashboard(windowMinutes: int = 60):
    """Near-real-time operational dashboard—aggregations over the last N minutes."""
    with get_session() as session:
        activity = session.execute(text(sql.OLTAP_ACTIVE_USERS), {"window_minutes": windowMinutes}).fetchone()
        by_status = session.execute(text(sql.OLTAP_BY_STATUS), {"window_minutes": windowMinutes}).fetchall()
        accts = session.execute(text(sql.OLTAP_ACCOUNT_SUMMARY)).fetchall()
    
    return {
        "windowMinutes": windowMinutes,
        "activity": dict(activity._mapping) if activity else {},
        "transactionsByStatus": [dict(r._mapping) for r in by_status],
        "accountSummary": [dict(r._mapping) for r in accts],
    }


@app.get("/olap/spend")
def olap_spend(
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
):
    from_iso = _iso_or_none(from_)
    to_iso = _iso_or_none(to)

    with get_session() as session:
        rows = session.execute(text(sql.OLAP_SPEND), {"from_date": from_iso, "to_date": to_iso}).fetchall()

    return {"from": from_iso or "all", "to": to_iso or "all", "rows": [dict(r._mapping) for r in rows]}


@app.get("/olap/analytics")
def olap_analytics(
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
):
    """Historical OLAP—deep analytics over time ranges."""
    from_iso = _iso_or_none(from_)
    to_iso = _iso_or_none(to)
    
    with get_session() as session:
        daily_trend = session.execute(text(sql.OLAP_DAILY_TREND), {"from_date": from_iso, "to_date": to_iso}).fetchall()
        user_profiles = session.execute(text(sql.OLAP_USER_PROFILES), {"from_date": from_iso, "to_date": to_iso}).fetchall()
        account_perf = session.execute(text(sql.OLAP_ACCOUNT_PERFORMANCE), {"from_date": from_iso, "to_date": to_iso}).fetchall()
    
    return {
        "from": from_iso or "all",
        "to": to_iso or "all",
        "dailyTrend": [dict(r._mapping) for r in daily_trend],
        "userProfiles": [dict(r._mapping) for r in user_profiles],
        "accountPerformance": [dict(r._mapping) for r in account_perf],
    }


@app.get("/olap/category-trends")
def olap_category_trends(
    from_: Optional[str] = Query(default=None, alias="from"),
    to: Optional[str] = None,
):
    """Category-level historical analysis with trends."""
    from_iso = _iso_or_none(from_)
    to_iso = _iso_or_none(to)
    
    with get_session() as session:
        categories = session.execute(text(sql.OLAP_CATEGORY_TRENDS), {"from_date": from_iso, "to_date": to_iso}).fetchall()
    
    return {
        "from": from_iso or "all",
        "to": to_iso or "all",
        "categories": [dict(r._mapping) for r in categories],
    }


# --- Agent Endpoints ---
@app.post("/agent/chat")
async def agent_chat(payload: dict):
    """Chat with the banking agent."""
    session_id = payload.get("session_id") or f"s_{uuid.uuid4().hex[:8]}"
    user_id = payload.get("user_id", "user_1")
    message = payload.get("message", "")
    
    if not message:
        return {"error": "Message required"}
    
    history = agent.get_chat_history(session_id)
    result = await agent.chat(session_id, user_id, message, history)
    
    if result.get("response"):
        trace_id = f"t_{uuid.uuid4().hex[:8]}"
        agent.save_chat_message(session_id, user_id, "human", message, trace_id)
        agent.save_chat_message(session_id, user_id, "ai", result["response"], trace_id)
    
    return result | {"session_id": session_id}


@app.get("/agent/sessions")
def agent_sessions(user_id: str = "user_1"):
    """Get chat sessions for a user."""
    sessions = agent.get_user_sessions(user_id)
    return {"sessions": sessions}


@app.get("/agent/history/{session_id}")
def agent_history(session_id: str):
    """Get chat history for a session."""
    history = agent.get_chat_history(session_id)
    return {"session_id": session_id, "messages": history}


@app.delete("/agent/session/{session_id}")
def agent_delete_session(session_id: str):
    """Delete a chat session and all its history."""
    with get_session() as session:
        session.execute(text(sql.DELETE_CHAT_HISTORY_BY_SESSION), {"sid": session_id})
        session.execute(text(sql.DELETE_CHAT_SESSION), {"sid": session_id})
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
