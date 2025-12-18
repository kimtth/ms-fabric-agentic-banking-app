CREATE VIEW session_duration_date AS
SELECT
    [CH1].[user_id],
    [CH1].[session_id],
    CAST([CH1].[created_at] AS DATE) AS [date],
    DATEDIFF(SECOND, [CH1].[created_at], [CH1].[updated_at]) AS [sess_duration]
FROM [dbo].[chat_sessions] AS [CH1];
GO

CREATE VIEW UserAsks AS
SELECT [CH1].[user_id], [CH1].[trace_id], [CH1].[content], [CH1].[session_id], [CH2].[response_time_seconds], [CH1].[date]
FROM
(SELECT
    [user_id],
    [trace_id],
    [content],
    [session_id],
    CAST([trace_end] AS DATE) AS [date]
FROM
    [dbo].[chat_history] as ch
WHERE [ch].[message_type] = 'human' ) AS CH1
JOIN (
SELECT
    trace_id,
    CASE
        WHEN [response_time_ms] IS NOT NULL THEN [response_time_ms] / 1000.0
        ELSE NULL
    END AS response_time_seconds
    FROM
    [chat_history]) AS CH2 ON [CH1].trace_id = CH2.trace_id
WHERE [CH2].[response_time_seconds] IS NOT NULL;
GO