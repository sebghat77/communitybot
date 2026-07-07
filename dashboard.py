from flask import Flask, render_template_string
from database import (
    get_evaluation_summary, get_channel_activity, get_user_activity,
    get_recommendation_stats, get_nudge_stats, get_recent_logs
)

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CommunityBot Dashboard</title>
<style>
body{margin:0;font-family:Arial,sans-serif;background:#0f172a;color:#e5e7eb}
.container{max-width:1200px;margin:auto;padding:32px}
h1{font-size:36px;margin-bottom:6px}
.subtitle{color:#94a3b8;margin-bottom:30px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card{background:#1e293b;border:1px solid #334155;border-radius:18px;padding:22px}
.metric{font-size:34px;font-weight:700;color:#38bdf8}
.label{color:#cbd5e1;margin-top:8px}
.section{margin-top:28px}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:12px;border-bottom:1px solid #334155;text-align:left}
th{color:#93c5fd}
.badge{display:inline-block;padding:5px 9px;border-radius:999px;background:#334155}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
<h1>CommunityBot Evaluation Dashboard</h1>
<div class="subtitle">Onboarding, recommendations, awareness nudges and participation logs.</div>

<div class="grid">
<div class="card"><div class="metric">{{summary.users_total}}</div><div class="label">Total users</div></div>
<div class="card"><div class="metric">{{summary.onboarding_completed}}</div><div class="label">Onboarding completed</div></div>
<div class="card"><div class="metric">{{summary.onboarding_rate}}%</div><div class="label">Onboarding rate</div></div>
<div class="card"><div class="metric">{{summary.recommendations_sent}}</div><div class="label">Recommendations sent</div></div>
<div class="card"><div class="metric">{{summary.recommendation_engagement_rate}}%</div><div class="label">Recommendation engagement</div></div>
<div class="card"><div class="metric">{{summary.nudge_engagement_rate}}%</div><div class="label">Nudge engagement</div></div>
</div>

<div class="section card"><h2>Most active channels</h2><table><tr><th>Channel</th><th>Messages</th></tr>
{% for name,count in channel_activity %}<tr><td>#{{name}}</td><td>{{count}}</td></tr>{% endfor %}
</table></div>

<div class="section card"><h2>Most active users</h2><table><tr><th>User</th><th>Messages</th></tr>
{% for name,count in user_activity %}<tr><td>{{name}}</td><td>{{count}}</td></tr>{% endfor %}
</table></div>

<div class="section card"><h2>Recommendation stats</h2><table><tr><th>Status</th><th>Count</th></tr>
{% for status,count in recommendation_stats %}<tr><td><span class="badge">{{status}}</span></td><td>{{count}}</td></tr>{% endfor %}
</table></div>

<div class="section card"><h2>Nudge stats</h2><table><tr><th>Type</th><th>Status</th><th>Count</th></tr>
{% for nudge_type,status,count in nudge_stats %}<tr><td><span class="badge">{{nudge_type}}</span></td><td>{{status}}</td><td>{{count}}</td></tr>{% endfor %}
</table></div>

<div class="section card"><h2>Recent logs</h2><table><tr><th>Time</th><th>User</th><th>Event</th><th>Value</th><th>Channel</th></tr>
{% for username,event_type,event_value,channel_name,timestamp in recent_logs %}
<tr><td>{{timestamp}}</td><td>{{username}}</td><td>{{event_type}}</td><td>{{event_value}}</td><td>#{{channel_name}}</td></tr>
{% endfor %}
</table></div>

</div>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(
        TEMPLATE,
        summary=get_evaluation_summary(),
        channel_activity=get_channel_activity(10),
        user_activity=get_user_activity(10),
        recommendation_stats=get_recommendation_stats(),
        nudge_stats=get_nudge_stats(),
        recent_logs=get_recent_logs(20)
    )


if __name__ == "__main__":
    app.run(debug=True)
