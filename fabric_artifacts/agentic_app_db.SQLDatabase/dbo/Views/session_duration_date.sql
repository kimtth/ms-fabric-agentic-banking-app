CREATE VIEW session_duration_date AS
SELECT
    [CH1].[user_id],
    [CH1].[session_id],
    CAST([CH1].[created_at] AS DATE) AS [date],
    DATEDIFF(SECOND, [CH1].[created_at], [CH1].[updated_at]) AS [sess_duration]
FROM [dbo].[chat_sessions] AS [CH1];

GO

