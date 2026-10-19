from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
import argparse, html, json

BASE = Path(__file__).parent

def load_json(name):
    with open(BASE / name, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_json("config.json")
ENTITIES = load_json("entities.json")
WALLET_INTEL = load_json("wallet_intelligence.json")
RPC_URL = CONFIG["rpc_url"]
ENTITY_BY_WALLET = {e["wallet"].lower(): e for e in ENTITIES}

def rpc(method, params=None):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params or [],"id":1}).encode("utf-8")
    req = Request(RPC_URL, data=payload, headers={"Content-Type":"application/json"})
    with urlopen(req, timeout=10) as response:
        body = json.loads(response.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(body["error"])
    return body["result"]

def entity_for(address):
    return ENTITY_BY_WALLET.get(address.lower()) if address else None

def label(address):
    if not address:
        return "Contract creation"
    entity = entity_for(address)
    return entity["name"] if entity else f"External {address[:10]}…"

def severity(score):
    if score >= 100: return "CRITICAL"
    if score >= 60: return "ALERT"
    if score >= 30: return "REVIEW"
    return "CLEAR"

def read_chain(from_block=0):
    latest = int(rpc("eth_blockNumber"), 16)
    rows = []
    for block_number in range(from_block, latest + 1):
        block = rpc("eth_getBlockByNumber", [hex(block_number), True])
        if not block: continue
        block_time = datetime.fromtimestamp(int(block["timestamp"], 16), tz=timezone.utc)
        for tx in block.get("transactions", []):
            if tx.get("to") is None: continue
            value_wei = int(tx["value"], 16)
            if value_wei == 0: continue
            rows.append({
                "hash": tx["hash"], "block": block_number, "timestamp": block_time,
                "from": tx["from"].lower(), "to": tx["to"].lower(),
                "amount_eth": value_wei / 10**18
            })
    rows.sort(key=lambda x: (x["timestamp"], x["block"]))
    return rows, latest

def evaluate(rows):
    results = []
    high_value = float(CONFIG["high_value_threshold_eth"])
    rapid_minutes = int(CONFIG["rapid_pass_through_minutes"])
    rapid_ratio = float(CONFIG["rapid_pass_through_ratio"])
    for tx in rows:
        score, reasons = 0, []
        sender, receiver = entity_for(tx["from"]), entity_for(tx["to"])
        if sender and sender["kyb_status"] != "APPROVED":
            score += 70; reasons.append("Sender KYB not approved")
        if receiver and receiver["kyb_status"] != "APPROVED":
            score += 70; reasons.append("Receiver KYB not approved")
        if receiver is None:
            score += 20; reasons.append("Destination not registered in KYB registry")
        if (sender and sender["risk_level"] == "HIGH") or (receiver and receiver["risk_level"] == "HIGH"):
            score += 30; reasons.append("High-risk entity involved")
        if tx["amount_eth"] >= high_value:
            score += 25; reasons.append(f"High-value transaction (>= {high_value:g} ETH)")
        intel = WALLET_INTEL.get(tx["to"])
        if intel:
            if int(intel.get("risk_score", 0)) >= 80:
                score += 50; reasons.append(f"High-risk destination wallet (mock risk {intel['risk_score']})")
            if intel.get("sanctions_match"):
                score += 100; reasons.append("Sanctions match (mock blockchain intelligence)")
            if intel.get("exposures"):
                reasons.append("Exposure: " + ", ".join(intel["exposures"]))
        for prev in results:
            if prev["to"] != tx["from"]: continue
            delta = tx["timestamp"] - prev["timestamp"]
            if timedelta(0) <= delta <= timedelta(minutes=rapid_minutes) and tx["amount_eth"] >= prev["amount_eth"] * rapid_ratio:
                score += 35
                reasons.append(f"Rapid pass-through after {prev['short_hash']} ({int(delta.total_seconds() // 60)} min)")
                break
        results.append({**tx,
            "short_hash": tx["hash"][:12] + "…",
            "sender_name": label(tx["from"]), "receiver_name": label(tx["to"]),
            "score": score, "status": severity(score),
            "reasons": reasons or ["No material risk indicators"]})
    return results

def render_html(rows, latest_block):
    counts = {}
    for r in rows: counts[r["status"]] = counts.get(r["status"], 0) + 1
    trs = []
    for r in rows:
        why = "<br>".join(html.escape(x) for x in r["reasons"])
        trs.append(f"<tr><td>{r['block']}</td><td title='{html.escape(r['hash'])}'>{html.escape(r['short_hash'])}</td><td>{html.escape(r['sender_name'])}</td><td>{html.escape(r['receiver_name'])}</td><td>{r['amount_eth']:,.4f} ETH</td><td>{r['score']}</td><td><strong>{r['status']}</strong></td><td>{why}</td></tr>")
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>Besu Compliance PoC</title><style>body{{font-family:Arial;margin:40px;background:#f6f7f8;color:#222}}.cards{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}}.card{{background:white;border:1px solid #ddd;border-radius:8px;padding:14px 18px}}.n{{font-size:26px;font-weight:bold}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{border:1px solid #ddd;padding:9px;text-align:left;vertical-align:top}}th{{background:#eee}}</style></head><body><h1>Digital Asset Compliance PoC</h1><p>Real Hyperledger Besu transactions + KYB/KYT rules + mock blockchain intelligence</p><div class='cards'><div class='card'>Latest block<div class='n'>{latest_block}</div></div><div class='card'>Transactions<div class='n'>{len(rows)}</div></div><div class='card'>Clear<div class='n'>{counts.get('CLEAR',0)}</div></div><div class='card'>Review<div class='n'>{counts.get('REVIEW',0)}</div></div><div class='card'>Alerts<div class='n'>{counts.get('ALERT',0)}</div></div><div class='card'>Critical<div class='n'>{counts.get('CRITICAL',0)}</div></div></div><table><thead><tr><th>Block</th><th>Tx hash</th><th>From</th><th>To</th><th>Amount</th><th>Risk</th><th>Status</th><th>Why?</th></tr></thead><tbody>{''.join(trs)}</tbody></table><p>On-chain transactions are real; KYB and blockchain-intelligence labels are simulated.</p></body></html>"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-block", type=int, default=0)
    args = parser.parse_args()
    print("Connecting to Besu:", RPC_URL)
    rows, latest = read_chain(args.from_block)
    results = evaluate(rows)
    print(f"Latest block: {latest}\nValue-transfer transactions found: {len(results)}\n")
    for r in results:
        print(f"Block {r['block']} | {r['short_hash']} | {r['sender_name']} -> {r['receiver_name']} | {r['amount_eth']:.4f} ETH | Score {r['score']} | {r['status']}")
        for reason in r["reasons"]: print("  -", reason)
        print()
    output = BASE / "report-besu.html"
    output.write_text(render_html(results, latest), encoding="utf-8")
    print("Report generated:", output)

if __name__ == "__main__":
    main()
