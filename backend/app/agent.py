"""Banking Agent using agent-framework with Azure OpenAI and SQLAlchemy tools."""
import json
import os
import re
import uuid
from typing import Optional

from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from sqlalchemy import inspect, text

from .db import get_session, engine
from . import sql


agent_client: Optional[ChatAgent] = None


def _ensure_agent() -> ChatAgent:
    global agent_client
    if agent_client:
        return agent_client
    chat_client = AzureOpenAIChatClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    )
    agent_client = ChatAgent(
        chat_client=chat_client,
        instructions="You are a concise banking assistant with read-only SQL access. Use tools to query banking data and provide insights.",
        tools=[list_tables, describe_table, run_query],
    )
    return agent_client


def init_agent() -> bool:
    try:
        _ensure_agent()
        return True
    except Exception:
        return False


# --- Tools ---
def list_tables() -> str:
    insp = inspect(engine)
    return json.dumps({"tables": insp.get_table_names(schema="dbo")})


def describe_table(table_name: str) -> str:
    insp = inspect(engine)
    cols = insp.get_columns(table_name, schema="dbo")
    if not cols:
        return json.dumps({"error": f"Table {table_name} not found"})
    return json.dumps(
        {
            "table": table_name,
            "columns": [
                {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)} for c in cols
            ],
        }
    )


def run_query(query: str, limit: int = 100) -> str:
    q = query.strip()
    if not q.lower().startswith("select"):
        return json.dumps({"error": "Only SELECT queries allowed"})
    if re.search(r"\b(drop|delete|update|insert|alter|truncate|create)\b", q, re.IGNORECASE):
        return json.dumps({"error": "Query contains prohibited keywords"})
    limit = max(1, min(limit, 500))
    if "top" not in q.lower():
        q = re.sub(r"^select", f"select top {limit}", q, flags=re.IGNORECASE)
    with get_session() as session:
        rows = session.execute(text(q)).mappings().all()
    return json.dumps({"row_count": len(rows), "rows": rows})


# --- Chat API helpers ---
async def chat(session_id: str, user_id: str, message: str, history: list | None = None) -> dict:
    agent = _ensure_agent()
    history = history or []
    result = await agent.run(message, chat_history=history)
    return {"response": str(result), "session_id": session_id}


def save_chat_message(session_id: str, user_id: str, msg_type: str, content: str, trace_id: Optional[str] = None):
    trace_id = trace_id or f"trace_{uuid.uuid4().hex[:8]}"
    with get_session() as session:
        session.execute(
            text(sql.UPSERT_CHAT_AND_HISTORY),
            {
                "sid": session_id,
                "uid": user_id,
                "mid": f"msg_{uuid.uuid4().hex[:12]}",
                "tid": trace_id,
                "mtype": msg_type,
                "content": content,
            },
        )


def get_chat_history(session_id: str, limit: int = 10) -> list:
    """Retrieve chat history for a session in chronological order (oldest first).
    
    Limits to most recent messages to avoid token overflow.
    """
    with get_session() as session:
        rows = session.execute(
            text(sql.GET_CHAT_HISTORY),
            {"lim": limit, "sid": session_id},
        ).all()
    # Reverse to get chronological order (oldest first) for agent context
    ordered = list(reversed(rows))
    history = [
        {
            "role": "user" if r[0] == "human" else "assistant",
            "content": r[1]
        }
        for r in ordered
    ]
    return history


def get_user_sessions(user_id: str) -> list:
    with get_session() as session:
        rows = session.execute(
            text(sql.GET_USER_SESSIONS),
            {"uid": user_id},
        ).mappings().all()
    return list(rows)
