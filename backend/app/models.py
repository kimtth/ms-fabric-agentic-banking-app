from datetime import datetime
from sqlalchemy import Column, String, DateTime, Numeric, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    accounts = relationship("Account", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False)
    account_number = Column(String(50), nullable=False)
    account_type = Column(String(50), nullable=False)
    balance = Column(Numeric(18, 2), default=0)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="accounts")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(255), primary_key=True)
    from_account_id = Column(String(255), ForeignKey("accounts.id"))
    to_account_id = Column(String(255), ForeignKey("accounts.id"))
    amount = Column(Numeric(18, 2), nullable=False)
    type = Column(String(50), nullable=False)
    description = Column(String(500))
    category = Column(String(100))
    status = Column(String(50), default="posted")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(String(255), primary_key=True)
    user_id = Column(String(255), nullable=False)
    title = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    duration_seconds = Column(Integer)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False)
    trace_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    agent_id = Column(String(255))
    message_type = Column(String(50), nullable=False)
    content = Column(Text)
    model_name = Column(String(255))
    content_filter_results = Column(Text)
    total_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    prompt_tokens = Column(Integer)
    finish_reason = Column(String(255))
    response_time_ms = Column(Integer)
    trace_end = Column(DateTime, default=datetime.utcnow)
    tool_call_id = Column(String(255))
    tool_name = Column(String(255))
    tool_input = Column(Text)
    tool_output = Column(Text)
    tool_id = Column(String(255))


class ToolUsage(Base):
    __tablename__ = "tool_usage"

    tool_call_id = Column(String(255), primary_key=True)
    session_id = Column(String(255), nullable=False)
    trace_id = Column(String(255))
    tool_id = Column(String(255), nullable=False)
    tool_name = Column(String(255), nullable=False)
    tool_input = Column(Text, nullable=False)
    tool_output = Column(Text)
    tool_message = Column(Text)
    status = Column(String(50))
    tokens_used = Column(Integer)
