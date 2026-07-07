import csv
import os
from database import (
    get_connection, init_db, get_evaluation_summary, get_channel_activity,
    get_user_activity, get_recommendation_stats, get_nudge_stats, get_event_counts
)

EXPORT_DIR = "exports"


def write_csv(filename, headers, rows):
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, filename)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Exported: {path}")


def export_table(table_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    headers = [description[0] for description in cur.description]
    conn.close()
    write_csv(f"{table_name}.csv", headers, rows)


def main():
    init_db()

    for table in ["users", "user_logs", "recommendations", "nudges"]:
        export_table(table)

    summary = get_evaluation_summary()
    write_csv("summary.csv", ["metric", "value"], [(key, value) for key, value in summary.items()])
    write_csv("channel_activity.csv", ["channel_name", "message_count"], get_channel_activity(100))
    write_csv("user_activity.csv", ["username", "message_count"], get_user_activity(100))
    write_csv("recommendation_stats.csv", ["status", "count"], get_recommendation_stats())
    write_csv("nudge_stats.csv", ["nudge_type", "status", "count"], get_nudge_stats())
    write_csv("event_counts.csv", ["event_type", "count"], get_event_counts())


if __name__ == "__main__":
    main()
