#!/usr/bin/env python3
"""
Digital Asset Compliance PoC - transaction-level rules engine.

Reads one confirmed transaction directly from the local Hyperledger Besu
network, maps blockchain addresses to known entities, enriches the sender
with optional Sumsub applicant metadata, applies simple demo risk rules,
and writes an auditable JSON compliance case.

This is a demonstration rules engine, not a production AML/KYT system.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from besu_monitor import BASE, CONFIG, entity_for, label, rpc


def load_sumsub_applicants():
    path = BASE / "sumsub_applicants.json"
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        rows = json.load(f)

    return {
        row["entityId"]: row
        for row in rows
        if row.get("entityId")
    }


def get_transaction(tx_hash):
    tx = rpc("eth_getTransactionByHash", [tx_hash])
    if tx is None:
        raise RuntimeError(f"Transaction not found in Besu: {tx_hash}")

    if not tx.get("blockNumber"):
        raise RuntimeError("Transaction has not been included in a block yet.")

    block = rpc("eth_getBlockByNumber", [tx["blockNumber"], False])
    if block is None:
        raise RuntimeError(f"Block {tx['blockNumber']} not found.")

    receipt = rpc("eth_getTransactionReceipt", [tx_hash])
    return tx, block, receipt


def evaluate_transaction(tx, receipt, amount_eth, sender, recipient):
    rules = []
    score = 0
    high_value = float(CONFIG.get("high_value_threshold_eth", 10))

    if amount_eth >= high_value:
        rules.append({
            "rule": "HIGH_VALUE_TRANSFER",
            "description": f"Transaction amount is {high_value:g} ETH or higher",
            "score": 60,
        })
        score += 60

    if recipient is None:
        rules.append({
            "rule": "UNKNOWN_COUNTERPARTY",
            "description": "Destination wallet is not mapped to a known entity",
            "score": 30,
        })
        score += 30

    if sender and sender.get("kyb_status") != "APPROVED":
        rules.append({
            "rule": "SENDER_KYB_NOT_APPROVED",
            "description": "Sender KYB status is not approved in the PoC registry",
            "score": 40,
        })
        score += 40

    if recipient and recipient.get("kyb_status") != "APPROVED":
        rules.append({
            "rule": "COUNTERPARTY_KYB_NOT_APPROVED",
            "description": "Counterparty KYB status is not approved in the PoC registry",
            "score": 40,
        })
        score += 40

    if (
        (sender and sender.get("risk_level") == "HIGH")
        or (recipient and recipient.get("risk_level") == "HIGH")
    ):
        rules.append({
            "rule": "HIGH_RISK_ENTITY",
            "description": "A high-risk entity is involved in the transaction",
            "score": 30,
        })
        score += 30

    receipt_status = None
    if receipt and receipt.get("status") is not None:
        receipt_status = int(receipt["status"], 16)
        if receipt_status == 0:
            rules.append({
                "rule": "FAILED_TRANSACTION",
                "description": "Blockchain transaction failed",
                "score": 40,
            })
            score += 40

    score = min(score, 100)

    if score >= 60:
        risk = "HIGH"
        decision = "MANUAL_REVIEW"
    elif score >= 30:
        risk = "MEDIUM"
        decision = "REVIEW_IF_NEEDED"
    else:
        risk = "LOW"
        decision = "ALLOW"

    return rules, score, risk, decision, receipt_status


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate one Besu transaction and create a compliance case."
    )
    parser.add_argument("--tx-hash", required=True, help="Besu transaction hash")
    args = parser.parse_args()

    tx_hash = args.tx_hash.strip()
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    tx, block, receipt = get_transaction(tx_hash)

    sender_address = tx["from"].lower()
    recipient_address = tx["to"].lower() if tx.get("to") else None

    if recipient_address is None:
        raise RuntimeError("Contract-creation transactions are not evaluated by this PoC.")

    sender = entity_for(sender_address)
    recipient = entity_for(recipient_address)
    amount_eth = int(tx["value"], 16) / 10**18
    block_number = int(tx["blockNumber"], 16)

    rules, score, risk, decision, receipt_status = evaluate_transaction(
        tx,
        receipt,
        amount_eth,
        sender,
        recipient,
    )

    sumsub_by_entity = load_sumsub_applicants()
    sender_entity_id = sender["id"] if sender else None
    sumsub_applicant = (
        sumsub_by_entity.get(sender_entity_id)
        if sender_entity_id
        else None
    )

    case = {
        "caseId": "CASE-" + tx_hash[2:10].upper(),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "transaction": {
            "hash": tx_hash,
            "block": block_number,
            "blockHash": block.get("hash"),
            "from": sender_address,
            "to": recipient_address,
            "amount": amount_eth,
            "currency": "ETH",
            "status": receipt_status,
        },
        "sender": {
            "entityId": sender_entity_id,
            "name": label(sender_address),
            "wallet": sender_address,
            "sumsub": sumsub_applicant,
        },
        "counterparty": {
            "entityId": recipient["id"] if recipient else None,
            "name": label(recipient_address),
            "wallet": recipient_address,
        },
        "riskAssessment": {
            "score": score,
            "risk": risk,
            "decision": decision,
            "triggeredRules": rules,
        },
        "network": {
            "name": "Hyperledger Besu Private",
            "chainId": 1337,
        },
    }

    print("\n====================================")
    print(" DIGITAL ASSET COMPLIANCE ALERT")
    print("====================================\n")
    print("Case ID:      ", case["caseId"])
    print("From:         ", case["sender"]["name"])
    print("To:           ", case["counterparty"]["name"])
    print("Amount:       ", amount_eth, "ETH")
    print("Block:        ", block_number)

    if sumsub_applicant:
        print("Sumsub ID:    ", sumsub_applicant.get("applicantId", "N/A"))
        print("KYC level:    ", sumsub_applicant.get("verificationLevel", "N/A"))
        print("Review status:", sumsub_applicant.get("reviewStatus", "N/A"))

    print("\nRisk score:   ", score, "/ 100")
    print("Risk level:   ", risk)
    print("Decision:     ", decision)

    print("\nRules triggered:")
    if not rules:
        print(" - None")
    else:
        for rule in rules:
            print(
                f" - {rule['rule']}: "
                f"{rule['description']} (+{rule['score']})"
            )

    cases_dir = Path(BASE) / "cases"
    cases_dir.mkdir(exist_ok=True)
    output = cases_dir / f"{case['caseId']}.json"

    with output.open("w", encoding="utf-8") as f:
        json.dump(case, f, indent=2, ensure_ascii=False)

    print("\nCompliance case saved:")
    print(output)


if __name__ == "__main__":
    main()
