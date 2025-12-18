"""
Generate sample chat history data for Power BI reporting demonstration.

This script creates realistic chat sessions and messages to demonstrate:
- Session duration patterns
- User query patterns
- Response time metrics
- Tool usage analytics
- Token consumption trends
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import List, Tuple
import random
import pyodbc
from dotenv import load_dotenv

load_dotenv()


# Sample queries for realistic chat history
SAMPLE_QUERIES = [
    "What is my current account balance?",
    "Show me my transactions from last month",
    "How much did I spend on groceries this quarter?",
    "Transfer $500 from checking to savings",
    "What are my top spending categories?",
    "Show me all pending transactions",
    "What was my largest transaction last week?",
    "How much did I spend on dining out in November?",
    "List all my recurring payments",
    "What is my total spending this year?",
    "Show me deposits over $1000",
    "How many transactions did I make yesterday?",
    "What's my average monthly spending?",
    "Show me all ATM withdrawals",
    "Compare my spending this month vs last month",
]

SAMPLE_RESPONSES = [
    "I found {count} transactions matching your criteria. Your total balance is ${amount}.",
    "Based on the data, you spent ${amount} in that category during the specified period.",
    "I've executed the query and found {count} results. Here's what I discovered:",
    "Your account shows {count} transactions. The analysis indicates:",
    "After reviewing your transaction history, I can see:",
]

# Tool names aligned with report filters (Tool Health visuals)
TOOL_NAMES = [
    "create_new_account",
    "get_transactions_summary",
    "get_user_accounts",
    "transfer_money",
    "search_support_documents",
]

MODEL_NAMES = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]


def get_connection():
    """Create database connection."""
    conn_str = os.getenv("FABRIC_SQL_CONNECTION_STRING")
    if not conn_str:
        raise ValueError("FABRIC_SQL_CONNECTION_STRING not set")
    return pyodbc.connect(conn_str, autocommit=True)


def generate_trace_id() -> str:
    """Generate a unique trace ID."""
    return f"trace_{uuid.uuid4().hex[:16]}"


def generate_session_data(
    user_count: int = 5, 
    sessions_per_user: int = 10
) -> List[Tuple]:
    """Generate sample chat sessions."""
    sessions = []
    start_date = datetime.now() - timedelta(days=90)
    
    for user_idx in range(1, user_count + 1):
        user_id = f"user_{user_idx:03d}"
        
        for session_idx in range(sessions_per_user):
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            
            # Vary session creation time over 90 days
            days_offset = random.randint(0, 89)
            hour_offset = random.randint(0, 23)
            created_at = start_date + timedelta(days=days_offset, hours=hour_offset)
            
            # Session duration: 1-30 minutes
            duration_minutes = random.randint(1, 30)
            updated_at = created_at + timedelta(minutes=duration_minutes)
            
            title = f"Banking Query Session {session_idx + 1}"
            
            sessions.append((
                session_id,
                user_id,
                title,
                created_at,
                updated_at
            ))
    
    return sessions


def generate_chat_history(sessions: List[Tuple], max_messages: int | None = None) -> Tuple[List[Tuple], List[Tuple]]:
    """Generate chat history messages and tool usage data.

    If `max_messages` is provided, the total number of messages emitted
    (across all sessions) will not exceed that cap.
    """
    messages = []
    tool_usages = []
    messages_count = 0
    
    for session in sessions:
        # Stop early if we've reached the global cap
        if max_messages is not None and messages_count >= max_messages:
            break
        session_id, user_id, title, created_at, updated_at = session
        
        # Each session has 3-8 message pairs (user query + AI response)
        num_exchanges = random.randint(3, 8)
        current_time = created_at
        
        for exchange_idx in range(num_exchanges):
            if max_messages is not None and messages_count >= max_messages:
                break
            trace_id = generate_trace_id()
            
            # User message (human)
            human_message_id = f"msg_{uuid.uuid4().hex[:16]}"
            query = random.choice(SAMPLE_QUERIES)
            
            if max_messages is None or messages_count < max_messages:
                messages.append((
                    human_message_id,
                    session_id,
                    trace_id,
                    user_id,
                    None,  # agent_id
                    "human",
                    query,
                    None,  # model_name
                    "{}",  # content_filter_results
                    None,  # total_tokens
                    None,  # completion_tokens
                    None,  # prompt_tokens
                    None,  # finish_reason
                    None,  # response_time_ms
                    current_time,
                    None,  # tool_call_id
                    None,  # tool_name
                    None,  # tool_input
                    None,  # tool_output
                    None   # tool_id
                ))
                messages_count += 1
            
            # AI response
            ai_message_id = f"msg_{uuid.uuid4().hex[:16]}"
            response_time_ms = random.randint(500, 5000)
            model_name = random.choice(MODEL_NAMES)
            
            # Token usage varies by model
            if "mini" in model_name:
                prompt_tokens = random.randint(100, 500)
                completion_tokens = random.randint(50, 300)
            else:
                prompt_tokens = random.randint(200, 800)
                completion_tokens = random.randint(100, 500)
            
            total_tokens = prompt_tokens + completion_tokens
            
            response = random.choice(SAMPLE_RESPONSES).format(
                count=random.randint(1, 50),
                amount=f"{random.randint(100, 5000):,.2f}"
            )
            
            # 70% chance of tool usage
            tool_call_id = None
            tool_name = None
            tool_input = None
            tool_output = None
            tool_id = None
            tool_tokens_used = None
            
            if random.random() < 0.7:
                tool_call_id = f"call_{uuid.uuid4().hex[:12]}"
                tool_name = random.choice(TOOL_NAMES)
                tool_id = f"tool_{uuid.uuid4().hex[:8]}"
                tool_input = f'{{"query": "{query[:50]}..."}}'
                tool_output = f'{{"status": "success", "rows": {random.randint(1, 100)}}}'
                
                # Add to tool_usages
                tool_tokens_used = random.randint(50, 200)
                tool_usages.append((
                    tool_call_id,
                    session_id,
                    trace_id,
                    tool_id,
                    tool_name,
                    tool_input,
                    tool_output,
                    "Tool executed successfully",
                    "completed",
                    tool_tokens_used  # tokens_used
                ))
            
            response_time = current_time + timedelta(milliseconds=response_time_ms)
            
            if max_messages is None or messages_count < max_messages:
                messages.append((
                    ai_message_id,
                    session_id,
                    trace_id,
                    user_id,
                    "banking_agent_v1",
                    "ai",
                    response,
                    model_name,
                    "{}",
                    total_tokens,
                    completion_tokens,
                    prompt_tokens,
                    "stop",
                    response_time_ms,
                    response_time,
                    tool_call_id,
                    tool_name,
                    tool_input,
                    tool_output,
                    tool_id
                ))
                messages_count += 1

            # If a tool was used, also emit a tool_result message so
            # non-'ai' message types have token usage for visuals.
            if tool_call_id is not None and (max_messages is None or messages_count < max_messages):
                tool_result_message_id = f"msg_{uuid.uuid4().hex[:16]}"
                tool_result_time = response_time + timedelta(milliseconds=random.randint(50, 300))
                tool_result_content = (
                    f"Tool '{tool_name}' returned: "
                    f"{(tool_output or '')[:120]}"
                )

                messages.append((
                    tool_result_message_id,
                    session_id,
                    trace_id,
                    user_id,
                    "banking_agent_v1",
                    "tool_result",
                    tool_result_content,
                    None,              # model_name
                    "{}",             # content_filter_results
                    tool_tokens_used or random.randint(10, 60),  # total_tokens
                    None,              # completion_tokens
                    None,              # prompt_tokens
                    "tool_completed", # finish_reason
                    None,              # response_time_ms
                    tool_result_time,  # trace_end
                    tool_call_id,
                    tool_name,
                    tool_input,
                    tool_output,
                    tool_id
                ))
                messages_count += 1
            
            # Move time forward for next exchange (30s - 2min between exchanges)
            current_time = response_time + timedelta(seconds=random.randint(30, 120))
    
    return messages, tool_usages


def _executemany_batched(cursor, sql: str, rows: List[Tuple], batch_size: int = 100) -> int:
    """Execute many in batches with progress indicators."""
    total_rows = len(rows)
    inserted = 0
    
    for i in range(0, total_rows, batch_size):
        batch = rows[i:i + batch_size]
        cursor.executemany(sql, batch)
        inserted += len(batch)
        
        # Progress indicator every 10 batches or at the end
        if (i // batch_size + 1) % 10 == 0 or inserted >= total_rows:
            print(f"    Progress: {inserted}/{total_rows} rows...", flush=True)
    
    return inserted


def insert_sessions(conn, sessions: List[Tuple]) -> int:
    """Insert chat sessions into database."""
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO dbo.chat_sessions 
        (session_id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    """
    count = _executemany_batched(cursor, insert_sql, sessions, batch_size=100)
    cursor.close()
    return count


def insert_messages(conn, messages: List[Tuple]) -> int:
    """Insert chat history messages into database."""
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO dbo.chat_history 
        (message_id, session_id, trace_id, user_id, agent_id, message_type, 
         content, model_name, content_filter_results, total_tokens, 
         completion_tokens, prompt_tokens, finish_reason, response_time_ms, 
         trace_end, tool_call_id, tool_name, tool_input, tool_output, tool_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    count = _executemany_batched(cursor, insert_sql, messages, batch_size=100)
    cursor.close()
    return count


def insert_tool_usages(conn, tool_usages: List[Tuple]) -> int:
    """Insert tool usage data into database."""
    cursor = conn.cursor()
    insert_sql = """
        INSERT INTO dbo.tool_usage 
        (tool_call_id, session_id, trace_id, tool_id, tool_name, 
         tool_input, tool_output, tool_message, status, tokens_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    count = _executemany_batched(cursor, insert_sql, tool_usages, batch_size=100)
    cursor.close()
    return count


def clear_existing_data(conn):
    """Clear existing chat data for clean demo."""
    cursor = conn.cursor()
    
    print("Clearing existing chat data...")
    cursor.execute("DELETE FROM dbo.tool_usage")
    cursor.execute("DELETE FROM dbo.chat_history")
    cursor.execute("DELETE FROM dbo.chat_sessions")
    
    cursor.close()
    print("Existing data cleared.")


def main():
    """Generate and insert sample chat history data."""
    print("=" * 60)
    print("Generating Sample Chat History Data")
    print("=" * 60)
    
    # Configuration
    USER_COUNT = 10
    SESSIONS_PER_USER = 15
    MAX_MESSAGES = 1000  # Global cap on total chat messages
    CLEAR_EXISTING = True  # Set to False to append instead of replace
    
    print("\nConfiguration:")
    print(f"  Users: {USER_COUNT}")
    print(f"  Sessions per user: {SESSIONS_PER_USER}")
    print(f"  Total sessions: {USER_COUNT * SESSIONS_PER_USER}")
    
    # Generate data
    print("\n[1/4] Generating chat sessions...")
    sessions = generate_session_data(USER_COUNT, SESSIONS_PER_USER)
    print(f"  Generated {len(sessions)} sessions")
    
    print("\n[2/4] Generating chat history and tool usage...")
    messages, tool_usages = generate_chat_history(sessions, max_messages=MAX_MESSAGES)
    print(f"  Generated {len(messages)} messages (cap={MAX_MESSAGES})")
    print(f"  Generated {len(tool_usages)} tool usage records")
    
    # Connect to database
    print("\n[3/4] Connecting to Fabric SQL database...")
    conn = get_connection()
    print("  Connected successfully")
    
    # Clear and insert
    print("\n[4/4] Inserting data...")
    import time
    start_time = time.time()
    
    if CLEAR_EXISTING:
        clear_existing_data(conn)
    else:
        print("  Appending to existing data (CLEAR_EXISTING=False)...")
    
    print("  Inserting sessions...")
    session_count = insert_sessions(conn, sessions)
    print(f"  ✓ Inserted {session_count} sessions")
    
    print("  Inserting chat messages (this may take 1-2 minutes)...")
    message_count = insert_messages(conn, messages)
    print(f"  ✓ Inserted {message_count} messages")
    
    print("  Inserting tool usage records...")
    tool_count = insert_tool_usages(conn, tool_usages)
    print(f"  ✓ Inserted {tool_count} tool usage records")
    
    elapsed = time.time() - start_time
    print(f"\n  Total insert time: {elapsed:.1f} seconds")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("Sample Data Generation Complete!")
    print("=" * 60)
    print("\nYou can now:")
    print("  - Query the views: session_duration_date, UserAsks")
    print("  - Build Power BI reports on agent performance")
    print("  - Analyze token usage, response times, and tool usage")


if __name__ == "__main__":
    main()
