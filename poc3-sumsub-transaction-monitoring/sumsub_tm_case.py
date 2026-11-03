#!/usr/bin/env python3
"""Persist Sumsub Sandbox TM responses alongside local Besu compliance cases.

The local riskAssessment field is intentionally preserved as an independent,
demonstrative decision. The Sumsub result is never overwritten with local scores.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def transaction_summary(response):
    """Print a concise summary without conflating local and Sumsub scores."""
    scoring = response.get("scoringResult") or {}
    review = response.get("review") or {}
    rules = scoring.get("matchedRules") or []
    print("Sumsub score:", scoring.get("score", response.get("score", "pending")))
    print("Sumsub reviewStatus:", review.get("reviewStatus", "pending"))
    print("Sumsub reviewAnswer:", (review.get("reviewResult") or {}).get("reviewAnswer", "N/A"))
    print("Sumsub matched rules:", len(rules))
    for rule in rules:
        print(" -", rule.get("title") or rule.get("name") or rule.get("id", "unnamed"))


def save_sumsub_result(tx_hash, response, applicant_id=None, stage="queried", payload=None):
    """Add evidence to an existing local case, or create a Sumsub-only case."""
    if not tx_hash.startswith("0x") or len(tx_hash) != 66:
        raise ValueError("Expected a full 0x-prefixed Ethereum transaction hash.")
    cases_dir = BASE / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    case_id = "CASE-" + tx_hash[2:10].upper()
    path = cases_dir / (case_id + ".json")
    if path.exists():
        with path.open("r", encoding="utf-8") as stream:
            case = json.load(stream)
        # Protect against mixing evidence from separate transactions.
        saved_hash = (case.get("transaction") or {}).get("hash")
        if saved_hash and saved_hash.lower() != tx_hash.lower():
            raise ValueError("Case file hash does not match the requested transaction.")
    else:
        case = {
            "caseId": case_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "transaction": {"hash": tx_hash},
            "network": {"name": "Hyperledger Besu Private", "chainId": 1337},
        }

    scoring = response.get("scoringResult") or {}
    review = response.get("review") or {}
    data = response.get("data") or {}
    existing_tm = case.get("sumsubTransactionMonitoring") or {}
    txn_id = (
        (payload or {}).get("txnId")
        or data.get("txnId")
        or existing_tm.get("txnId")
    )
    result = {
        "provider": "Sumsub",
        "environment": "sandbox",
        "stage": stage,
        "lastUpdatedAt": datetime.now(timezone.utc).isoformat(),
        "applicantId": applicant_id or existing_tm.get("applicantId"),
        "txnId": txn_id,
        "sumsubTxnId": response.get("id") or response.get("kytTxnId")
        or existing_tm.get("sumsubTxnId"),
        "score": scoring.get("score", response.get("score")),
        "reviewStatus": review.get("reviewStatus"),
        "reviewAnswer": (review.get("reviewResult") or {}).get("reviewAnswer"),
        "matchedRules": scoring.get("matchedRules", []),
        "response": response,
    }
    if payload:
        result["submittedPayload"] = payload
    elif existing_tm.get("submittedPayload"):
        result["submittedPayload"] = existing_tm["submittedPayload"]
    # Compact, append-only status timeline. It preserves a prior onHold
    # observation when the analyst later approves or rejects the transaction.
    def snapshot(tm, observed_at=None):
        return {
            "observedAt": observed_at or tm.get("lastUpdatedAt"),
            "score": tm.get("score"),
            "reviewStatus": tm.get("reviewStatus"),
            "reviewAnswer": tm.get("reviewAnswer"),
            "matchedRuleNames": [
                r.get("title") or r.get("name") or r.get("id")
                for r in (tm.get("matchedRules") or [])
            ],
        }

    history = case.get("sumsubMonitoringTimeline") or []
    if not history and existing_tm.get("reviewStatus"):
        history.append(snapshot(existing_tm))

    new_snapshot = snapshot(result)
    tracked = ("score", "reviewStatus", "reviewAnswer", "matchedRuleNames")
    if not history or any(history[-1].get(k) != new_snapshot[k] for k in tracked):
        history.append(new_snapshot)
    case["sumsubMonitoringTimeline"] = history
    case["sumsubTransactionMonitoring"] = result

    # File is local and excluded from version control by .gitignore.
    temporary = path.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(case, stream, ensure_ascii=False, indent=2)
    temporary.replace(path)
    return path
