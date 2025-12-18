"""Centralized SQL statements for the banking app (SQLAlchemy text() compatible)."""

# OLTP
LIST_USERS = "select top (200) id, name, email from dbo.users order by created_at desc"
CREATE_USER = "insert into dbo.users (id, name, email) values (:id, :name, :email)"

LIST_ACCOUNTS = (
	"select top (200) id, user_id as userId, account_number as accountNumber, "
	"account_type as accountType, cast(balance as float) as balance, name "
	"from dbo.accounts order by created_at desc"
)
CREATE_ACCOUNT = (
	"insert into dbo.accounts (id, user_id, account_number, account_type, balance, name) "
	"values (:id, :user_id, :account_number, :account_type, :balance, :name)"
)

TRANSFER_DEBIT = "update dbo.accounts set balance = balance - :amount where id = :id"
TRANSFER_CREDIT = "update dbo.accounts set balance = balance + :amount where id = :id"
INSERT_TRANSACTION = (
	"insert into dbo.transactions (id, from_account_id, to_account_id, amount, type, description, category, status) "
	"values (:id, :from_account_id, :to_account_id, :amount, :type, :description, :category, :status)"
)

# OLTAP
OLTAP_SUMMARY = (
	"select count(*) as transactions, cast(coalesce(sum(amount), 0) as float) as totalAmount "
	"from dbo.transactions where created_at >= dateadd(minute, -:window_minutes, sysdatetimeoffset())"
)
OLTAP_TOP_CATEGORIES = (
	"select top (5) coalesce(category, '') as category, cast(sum(amount) as float) as amount "
	"from dbo.transactions where created_at >= dateadd(minute, -:window_minutes, sysdatetimeoffset()) "
	"group by category order by sum(amount) desc"
)

OLTAP_ACTIVE_USERS = (
	"select count(distinct from_account_id) as active_senders, "
	"count(distinct to_account_id) as active_receivers "
	"from dbo.transactions where created_at >= dateadd(minute, -:window_minutes, sysdatetimeoffset())"
)
OLTAP_BY_STATUS = (
	"select status, count(*) as count, cast(sum(amount) as float) as total_amount "
	"from dbo.transactions where created_at >= dateadd(minute, -:window_minutes, sysdatetimeoffset()) "
	"group by status"
)
OLTAP_ACCOUNT_SUMMARY = (
	"select account_type, count(*) as num_accounts, "
	"cast(avg(cast(balance as float)) as float) as avg_balance, "
	"cast(min(cast(balance as float)) as float) as min_balance, "
	"cast(max(cast(balance as float)) as float) as max_balance "
	"from dbo.accounts group by account_type"
)

# OLAP
OLAP_SPEND = (
	"select coalesce(category, '') as category, count(*) as transactions, cast(sum(amount) as float) as amount "
	"from dbo.transactions "
	"where (:from_date is null or created_at >= :from_date) and (:to_date is null or created_at <= :to_date) "
	"group by category order by sum(amount) desc"
)

OLAP_DAILY_TREND = (
	"select cast(created_at as date) as date, count(*) as txn_count, "
	"cast(sum(amount) as float) as total_volume "
	"from dbo.transactions "
	"where (:from_date is null or created_at >= :from_date) and (:to_date is null or created_at <= :to_date) "
	"group by cast(created_at as date) "
	"order by date desc"
)
OLAP_USER_PROFILES = (
	"select u.id, u.name, count(t.id) as transaction_count, "
	"cast(sum(t.amount) as float) as total_spent "
	"from dbo.users u "
	"left join dbo.accounts a on u.id = a.user_id "
	"left join dbo.transactions t on a.id = t.from_account_id "
	"where (:from_date is null or t.created_at >= :from_date) and (:to_date is null or t.created_at <= :to_date) "
	"group by u.id, u.name "
	"order by total_spent desc"
)
OLAP_ACCOUNT_PERFORMANCE = (
	"select a.id, a.name, count(t.id) as txn_count, "
	"cast(sum(t.amount) as float) as flow_volume, "
	"cast(a.balance as float) as current_balance "
	"from dbo.accounts a "
	"left join dbo.transactions t on a.id = t.from_account_id "
	"where (:from_date is null or t.created_at >= :from_date) and (:to_date is null or t.created_at <= :to_date) "
	"group by a.id, a.name, a.balance "
	"order by flow_volume desc"
)

OLAP_CATEGORY_TRENDS = (
	"select coalesce(category, 'Uncategorized') as category, "
	"count(*) as transaction_count, cast(sum(amount) as float) as total_amount, "
	"cast(avg(amount) as float) as avg_transaction "
	"from dbo.transactions "
	"where (:from_date is null or created_at >= :from_date) and (:to_date is null or created_at <= :to_date) "
	"group by category "
	"order by total_amount desc"
)

# Agent (chat) SQL
# Ensure session exists and append a message in a single batch
UPSERT_CHAT_AND_HISTORY = (
	"MERGE dbo.chat_sessions AS t "
	"USING (SELECT :sid AS session_id, :uid AS user_id) AS s "
	"ON t.session_id = s.session_id "
	"WHEN MATCHED THEN UPDATE SET updated_at = sysdatetimeoffset() "
	"WHEN NOT MATCHED THEN "
	"  INSERT (session_id, user_id, title, created_at, updated_at) "
	"  VALUES (s.session_id, s.user_id, 'Session ' + CONVERT(varchar(24), sysdatetimeoffset(), 121), sysdatetimeoffset(), sysdatetimeoffset()); "
	"INSERT INTO dbo.chat_history (message_id, session_id, trace_id, user_id, message_type, content, trace_end) "
	"VALUES (:mid, :sid, :tid, :uid, :mtype, :content, sysdatetimeoffset());"
)

GET_CHAT_HISTORY = (
	"SELECT TOP (:lim) message_type, content "
	"FROM dbo.chat_history WHERE session_id = :sid "
	"ORDER BY trace_end DESC"
)

GET_USER_SESSIONS = (
	"SELECT TOP (50) session_id, user_id, updated_at "
	"FROM dbo.chat_sessions WHERE user_id = :uid "
	"ORDER BY updated_at DESC"
)

DELETE_CHAT_HISTORY_BY_SESSION = "DELETE FROM dbo.chat_history WHERE session_id = :sid"
DELETE_CHAT_SESSION = "DELETE FROM dbo.chat_sessions WHERE session_id = :sid"
