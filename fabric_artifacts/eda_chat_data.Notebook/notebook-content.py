# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "791e7237-7faf-4bc5-9a98-01e7ae0e4a6f",
# META       "default_lakehouse_name": "agentic_lake",
# META       "default_lakehouse_workspace_id": "55270c15-e8b9-40bd-8c27-3b7c4e631d17",
# META       "known_lakehouses": [
# META         {
# META           "id": "791e7237-7faf-4bc5-9a98-01e7ae0e4a6f"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # EDA for Chat Demo: Metrics for Power BI + Lake EDA
# 
# This notebook computes filtered aggregates used by the Power BI visuals (Task 1) and performs exploratory data analysis over the lake data copied from the SQL database (Task 2).

# MARKDOWN ********************

# ## Imports and Configuration
# - Uses `pyodbc` + `pandas`
# - Defines output lake locations under `data/metrics/` for aggregates.

# CELL ********************

# Imports and configuration
from pathlib import Path
import pandas as pd
import numpy as np

# Lake output base (relative to repo root)
LAKE_BASE = Path("/lakehouse/default/Files/eda")
LAKE_BASE.mkdir(parents=True, exist_ok=True)

print(f"Metrics lake base: {LAKE_BASE}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Load Source Tables (SQL) for Metrics
# - Pull minimal columns from `dbo.chat_history` and `dbo.tool_usage` using `pyodbc`.
# - Convert `trace_end` to pandas datetime.

# CELL ********************

# Load source tables (minimal columns) from SQL
cols_chat = [
    "message_id","session_id","trace_id","user_id","message_type",
    "total_tokens","prompt_tokens","completion_tokens",
    "response_time_ms","trace_end","tool_call_id","tool_name"
]
cols_tool = ["tool_call_id","session_id","trace_id","tool_name","status"]

query_chat = f"SELECT {', '.join(cols_chat)} FROM dbo.chat_history"
query_tool = f"SELECT {', '.join(cols_tool)} FROM dbo.tool_usage"

# If your SQL query targets tables in the data lake, Spark is required. 
# If your SQL query targets the data warehouse, pandas can query it directly.
try:
    chat_history = spark.sql(query_chat).toPandas()
    tool_usage   = spark.sql(query_tool).toPandas()
except NameError:
    # Fallback: query the data warehouse via ODBC when Spark isn't available
    import os
    try:
        import pyodbc
    except Exception as e:
        raise RuntimeError("Spark session not found and 'pyodbc' is unavailable; install pyodbc or run in Fabric.") from e
    conn_str = os.getenv("FABRIC_SQL_ODBC_CONN_STR") or os.getenv("FABRIC_SQL_CONNECTION_STRING")
    if not conn_str:
        raise RuntimeError("Set FABRIC_SQL_ODBC_CONN_STR (ODBC connection string) to query the warehouse when Spark is unavailable.")
    with pyodbc.connect(conn_str) as conn:
        chat_history = pd.read_sql(query_chat, conn)
        tool_usage   = pd.read_sql(query_tool, conn)

# Type conversions
chat_history["trace_end"] = pd.to_datetime(chat_history["trace_end"], errors="coerce")
chat_history["message_type"] = chat_history["message_type"].astype("string")
chat_history["tool_name"] = chat_history["tool_name"].astype("string")

tool_usage["tool_name"] = tool_usage["tool_name"].astype("string")
tool_usage["status"] = tool_usage["status"].astype("string")

print("Loaded:")
print(" chat_history:", chat_history.shape)
print(" tool_usage:", tool_usage.shape)
chat_history.head(3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Build Daily Date Columns
# Create a `date` column normalized to midnight, using `trace_end` and dropping null dates.

# CELL ********************

# Build date column
chat_history = chat_history.copy()
chat_history["date"] = chat_history["trace_end"].dt.normalize()

# Drop rows without a date (to align with report slicers)
chat_history = chat_history.dropna(subset=["date"])  # ensures no NaT dates
chat_history["date"] = chat_history["date"].dt.date  # cast to date for PBI friendliness

print("Min/Max date:", chat_history["date"].min(), chat_history["date"].max())
chat_history.head(3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## “% of User Questions answered by tool usage”
# Filter: `message_type` is not `human` and not `tool_result`. Numerator = rows with tool (non-null `tool_call_id` or present in `tool_usage` by `trace_id`). Denominator = all filtered rows. Grouped daily.

# CELL ********************

# Compute % of user questions answered by tool usage
ai_like = chat_history[~chat_history["message_type"].isin(["human", "tool_result"])]

# Determine which traces used a tool (by tool_call_id on row OR matching trace_id in tool_usage)
has_tool_direct = ai_like["tool_call_id"].notna()
has_tool_via_usage = ai_like["trace_id"].isin(tool_usage["trace_id"].dropna().unique())
ai_like = ai_like.assign(has_tool = (has_tool_direct | has_tool_via_usage))

# Daily aggregates
daily_ai = ai_like.groupby("date", as_index=False).agg(
    ai_total=("trace_id", "count"),
    ai_with_tool=("has_tool", "sum")
)
daily_ai["pct_ai_answered_by_tool"] = (
    daily_ai["ai_with_tool"].astype(float) / daily_ai["ai_total"].replace(0, np.nan)
)

# Overall summary
overall_ai = pd.DataFrame({
    "ai_total": [int(ai_like.shape[0])],
    "ai_with_tool": [int(ai_like["has_tool"].sum())]
})
overall_ai["pct_ai_answered_by_tool"] = (
    overall_ai["ai_with_tool"].astype(float) / overall_ai["ai_total"].replace(0, np.nan)
)

print("Daily % rows:", daily_ai.shape)
print("Overall %:")
daily_ai.head(3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## “Token Usage by Message Type” (exclude `ai`)
# Group by `date` and `message_type`, summing `total_tokens`, excluding `ai`. Provide a pivot for quick validation.

# CELL ********************

# Token usage by message type (exclude 'ai')
df_non_ai = chat_history[chat_history["message_type"] != "ai"].copy()
df_non_ai["total_tokens"] = df_non_ai["total_tokens"].fillna(0)

agg_tokens = (
    df_non_ai.groupby(["date", "message_type"], as_index=False)["total_tokens"].sum()
)

pivot_tokens = agg_tokens.pivot(index="date", columns="message_type", values="total_tokens").fillna(0)
print("Aggregated token usage (long):", agg_tokens.shape)
agg_tokens.head(3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Tool Health for Selected Tools
# Filter to `{'create_new_account','get_transactions_summary','get_user_accounts','transfer_money'}` and compute counts by `status` and error rates.

# CELL ********************

# Tool Health for selected tools
selected_tools = {"create_new_account","get_transactions_summary","get_user_accounts","transfer_money"}

th = tool_usage[tool_usage["tool_name"].isin(selected_tools)].copy()
th["status"] = th["status"].fillna("unknown").astype("string")

# Counts by tool and status
health_counts = (
    th.groupby(["tool_name","status"], as_index=False)
      .agg(calls=("trace_id","count"))
)

# Error rates per tool: errored / total per tool
per_tool = th.groupby("tool_name", as_index=False).agg(total=("trace_id","count"))
errors = (
    th[th["status"].str.lower().isin(["error","failed","failure"])]
      .groupby("tool_name", as_index=False)
      .agg(errored=("trace_id","count"))
)
per_tool = per_tool.merge(errors, on="tool_name", how="left").fillna({"errored":0})
per_tool["error_rate_per_tool"] = per_tool["errored"].astype(float) / per_tool["total"].replace(0, np.nan)

print("Health counts:", health_counts.shape)
health_counts.head(3)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Persist Aggregates to Lake (CSV/Parquet) and Quick Validation
# Write outputs to `data/metrics/` with date-friendly types for Power BI. Then print heads and row counts.

# CELL ********************

# Persist aggregates to lake
from datetime import datetime
run_ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

# Create versioned folders
pct_dir = LAKE_BASE / "pct_ai_with_tool" / run_ts
tokens_dir = LAKE_BASE / "token_usage_by_message_type" / run_ts
health_dir = LAKE_BASE / "tool_health" / run_ts
for d in [pct_dir, tokens_dir, health_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Write
(daily_ai.assign(date=pd.to_datetime(daily_ai["date"]))
 .to_parquet(pct_dir / "daily_pct.parquet", index=False))
(daily_ai.assign(date=pd.to_datetime(daily_ai["date"]))
 .to_csv(pct_dir / "daily_pct.csv", index=False))

overall_ai.to_parquet(pct_dir / "overall_pct.parquet", index=False)
overall_ai.to_csv(pct_dir / "overall_pct.csv", index=False)

(agg_tokens.assign(date=pd.to_datetime(agg_tokens["date"]))
 .to_parquet(tokens_dir / "tokens.parquet", index=False))
(agg_tokens.assign(date=pd.to_datetime(agg_tokens["date"]))
 .to_csv(tokens_dir / "tokens.csv", index=False))

health_counts.to_parquet(health_dir / "health_counts.parquet", index=False)
health_counts.to_csv(health_dir / "health_counts.csv", index=False)
per_tool.to_parquet(health_dir / "per_tool.parquet", index=False)
per_tool.to_csv(health_dir / "per_tool.csv", index=False)

print("Wrote:")
print(" ", pct_dir)
print(" ", tokens_dir)
print(" ", health_dir)

# Quick validation
assert daily_ai.shape[0] > 0, "No daily rows for % answered by tool"
assert agg_tokens.shape[0] > 0, "No rows for token usage (non-ai)"
assert set(health_counts["tool_name"]) <= {"create_new_account","get_transactions_summary","get_user_accounts","transfer_money"}, "Unexpected tool names present"

print("Validation complete.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
