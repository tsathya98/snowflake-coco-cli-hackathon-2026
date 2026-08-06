-- ---------------------------------------------------------------------------
-- Warrant :: 46_schedule
--
-- Makes unattended operation visible instead of merely claimed.
--
-- "Operates with minimal manual intervention" is easy to assert and hard to
-- show. Two tasks run this pipeline without anybody present:
--
--   EXECUTE_ON_APPROVAL  triggered on a stream. A human approves in the console
--                        and this fires within the minute, re-resolving authority
--                        before it binds anything. Running since provisioning.
--   SCAN_FOR_EXCEPTIONS  hourly sweep. Left SUSPENDED by 40_orchestration.sql on
--                        purpose — an hourly loop starting the moment a reviewer
--                        runs setup would burn their trial credits unattended and
--                        mutate the demo data between their reading the
--                        walkthrough and following it.
--
-- TASK_ACTIVITY() reports what those tasks actually did. It exists as a procedure
-- rather than a view because INFORMATION_SCHEMA.TASK_HISTORY is a table function
-- returning every task in the account — including Snowflake's own housekeeping —
-- and an owner's-rights procedure can filter it to ours and hand the result to a
-- role that could not call the function itself.
--
-- Run after 45_review.sql. Requires the WARRANT_ROLE that owns the tasks.
-- ---------------------------------------------------------------------------

USE ROLE WARRANT_ROLE;
USE SCHEMA WARRANT.CORE;

CREATE OR REPLACE PROCEDURE TASK_ACTIVITY(hours NUMBER)
  RETURNS STRING
  LANGUAGE PYTHON
  RUNTIME_VERSION = '3.11'
  PACKAGES = ('snowflake-snowpark-python')
  HANDLER = 'main'
  COMMENT = 'What the scheduled and triggered tasks did, without a human present'
AS $$
import json

# Module constant, values bound. The same rule tools/lint_sql_boundary.py enforces
# across the Python package: statements are constants, values bind.
HISTORY = """
SELECT name,
       state,
       TO_VARCHAR(scheduled_time, 'YYYY-MM-DD HH24:MI:SS')  AS scheduled_time,
       TO_VARCHAR(completed_time, 'YYYY-MM-DD HH24:MI:SS')  AS completed_time,
       COALESCE(error_message, '')                           AS error_message
  FROM TABLE(WARRANT.INFORMATION_SCHEMA.TASK_HISTORY(
         SCHEDULED_TIME_RANGE_START => DATEADD(hour, ?, CURRENT_TIMESTAMP()),
         RESULT_LIMIT => 200))
 WHERE name IN ('SCAN_FOR_EXCEPTIONS', 'EXECUTE_ON_APPROVAL')
 ORDER BY scheduled_time DESC
"""

STATE = "SHOW TASKS IN SCHEMA WARRANT.CORE"


def main(session, hours):
    """Report unattended task activity over a recent window.

    Args:
        session: The implicit Snowpark session.
        hours: How far back to look. Passed negative to DATEADD.

    Returns:
        JSON with each task's current state and its recent runs, bucketed by task
        state. Skipped runs are reported in their own column rather than folded
        into either success or failure: for a triggered task, "the stream was
        empty so I spent nothing" is the common case and is neither.
    """
    window = -abs(int(hours or 24))
    runs = [row.as_dict() for row in session.sql(HISTORY, params=[window]).collect()]

    session.sql(STATE).collect()
    states = {
        row["name"]: row["state"]
        for row in session.sql(
            "SELECT \"name\", \"state\" FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))"
        ).collect()
        if row["name"] in ("SCAN_FOR_EXCEPTIONS", "EXECUTE_ON_APPROVAL")
    }

    # Bucket by STATE, never by "does it carry a message".
    #
    # A SKIPPED run carries the message "Conditional expression for task evaluated to
    # false", which is not a failure — it is EXECUTE_ON_APPROVAL finding the approval
    # stream empty and declining to spend anything. Counting it as failed reported 22
    # failures out of 41 on a pipeline that was working correctly.
    #
    # A SCHEDULED run has not happened yet and is neither.
    def count(*states):
        return len([r for r in runs if r["STATE"] in states])

    return json.dumps(
        {
            "window_hours": abs(window),
            "tasks": [
                {
                    "name": name,
                    "state": state,
                    "role": (
                        "triggered on the approval stream"
                        if name == "EXECUTE_ON_APPROVAL"
                        else "hourly sweep"
                    ),
                }
                for name, state in sorted(states.items())
            ],
            "runs": runs[:40],
            "summary": {
                "runs": len(runs),
                "succeeded": count("SUCCEEDED"),
                # Reported separately rather than folded into either column: the
                # cheap no-op is the common case for a triggered task and reading it
                # as a failure, or as a success, both mislead.
                "skipped_nothing_to_do": count("SKIPPED"),
                "failed": count("FAILED", "FAILED_AND_AUTO_SUSPENDED"),
                "pending": count("SCHEDULED"),
                "unattended": True,
            },
        }
    )
$$;

GRANT USAGE ON PROCEDURE WARRANT.CORE.TASK_ACTIVITY(NUMBER) TO ROLE WARRANT_PUBLIC;

SELECT 'Warrant :: 46_schedule complete' AS status;
