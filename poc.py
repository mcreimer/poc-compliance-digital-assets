from pathlib import Path
from datetime import datetime, timedelta
import json
import html

BASE = Path(__file__).parent

def load_json(name):
    with open(BASE / name, "r", encoding="utf-8") as f:
        return json.load(f)

entities = load_json("entities.json")
transactions = load_json("transactions.json")
entity_map = {e["id"]: e for e in entities}

def severity(score):
    if score >= 100:
        return "CRITICAL"
    if score >= 60:
        return "ALERT"
    if score >= 30:
        return "REVIEW"
    return "CLEAR"

def evaluate_transaction(tx, previous_transactions):
    score = 0
    reasons = []

    sender = entity_map[tx["from"]]
    receiver = entity_map[tx["to"]]

    # KYB
    if sender["kyb_status"] != "APPROVED":
        score += 70
        reasons.append("Sender KYB not approved")

    if receiver["kyb_status"] != "APPROVED":
        score += 70
        reasons.append("Receiver KYB not approved")

    # Entity risk
    if sender["risk_level"] == "HIGH" or receiver["risk_level"] == "HIGH":
        score += 30
        reasons.append("High-risk entity involved")

    # High value
    if tx["amount_brl"] >= 100000:
        score += 25
        reasons.append("High-value transaction")

    # Mock blockchain analytics
    if tx["destination_risk"] >= 80:
        score += 50
        reasons.append("High-risk destination wallet")

    if tx["sanctions_match"]:
        score += 100
        reasons.append("Sanctions match")

    # Rapid pass-through:
    # receiver of a recent transaction becomes sender within 15 minutes
    current_time = datetime.fromisoformat(tx["timestamp"])
    for prev in previous_transactions:
        prev_time = datetime.fromisoformat(prev["timestamp"])
        if (
            prev["to"] == tx["from"]
            and timedelta(0) <= current_time - prev_time <= timedelta(minutes=15)
            and tx["amount_brl"] >= prev["amount_brl"] * 0.75
        ):
            score += 35
            reasons.append(
                f"Rapid pass-through after {prev['id']}"
            )
            break

    return {
        **tx,
        "sender_name": sender["name"],
        "receiver_name": receiver["name"],
        "score": score,
        "status": severity(score),
        "reasons": reasons or ["No material risk indicators"]
    }

results = []
for tx in transactions:
    result = evaluate_transaction(tx, transactions[:len(results)])
    results.append(result)

print("\n=== SIMPLE CRYPTO COMPLIANCE POC ===\n")

for r in results:
    print(
        f"{r['id']} | {r['sender_name']} -> {r['receiver_name']} | "
        f"R$ {r['amount_brl']:,.2f} | Score {r['score']} | {r['status']}"
    )
    for reason in r["reasons"]:
        print(f"  - {reason}")
    print()

def render_report(rows):
    table_rows = []
    for r in rows:
        reasons = "<br>".join(html.escape(x) for x in r["reasons"])
        table_rows.append(f"""
        <tr>
            <td>{html.escape(r['id'])}</td>
            <td>{html.escape(r['sender_name'])}</td>
            <td>{html.escape(r['receiver_name'])}</td>
            <td>R$ {r['amount_brl']:,.2f}</td>
            <td>{r['score']}</td>
            <td><strong>{html.escape(r['status'])}</strong></td>
            <td>{reasons}</td>
        </tr>
        """)

    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Simple Crypto Compliance PoC</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    background: #f7f7f7;
    color: #222;
}}
h1 {{ margin-bottom: 4px; }}
.subtitle {{ color: #666; margin-bottom: 24px; }}
.cards {{
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
}}
.card {{
    background: white;
    padding: 16px 20px;
    border: 1px solid #ddd;
    border-radius: 8px;
    min-width: 110px;
}}
.card .number {{
    font-size: 28px;
    font-weight: bold;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}
th, td {{
    border: 1px solid #ddd;
    padding: 10px;
    text-align: left;
    vertical-align: top;
}}
th {{ background: #eee; }}
.note {{
    margin-top: 24px;
    padding: 14px;
    background: white;
    border-left: 4px solid #555;
}}
</style>
</head>
<body>
<h1>Digital Asset Compliance PoC</h1>
<div class="subtitle">KYB + KYT + Transaction Monitoring + Mock Blockchain Intelligence</div>

<div class="cards">
  <div class="card"><div>Total</div><div class="number">{len(rows)}</div></div>
  <div class="card"><div>Clear</div><div class="number">{counts.get('CLEAR', 0)}</div></div>
  <div class="card"><div>Review</div><div class="number">{counts.get('REVIEW', 0)}</div></div>
  <div class="card"><div>Alerts</div><div class="number">{counts.get('ALERT', 0)}</div></div>
  <div class="card"><div>Critical</div><div class="number">{counts.get('CRITICAL', 0)}</div></div>
</div>

<table>
<thead>
<tr>
<th>Transaction</th>
<th>From</th>
<th>To</th>
<th>Amount</th>
<th>Risk Score</th>
<th>Status</th>
<th>Why?</th>
</tr>
</thead>
<tbody>
{''.join(table_rows)}
</tbody>
</table>

<div class="note">
<strong>PoC simplification:</strong>
these transactions are simulated. In the next phase, the same compliance engine
can receive real events from a Hyperledger Besu network.
</div>

</body>
</html>"""

report = render_report(results)
report_path = BASE / "report.html"
report_path.write_text(report, encoding="utf-8")

print(f"HTML report generated: {report_path}")
