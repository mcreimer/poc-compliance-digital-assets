#!/usr/bin/env python3
"""Fetch a previously submitted Besu transaction's Sumsub Sandbox TM result."""
import argparse
import json
import os
import re
import sys
from urllib.parse import quote

from sumsub_client import request as sumsub_request
from sumsub_tm_case import save_sumsub_result, transaction_summary


def main():
    parser = argparse.ArgumentParser(
        description="Consulta o TM real da Sumsub por txnId e atualiza o case local."
    )
    parser.add_argument("--tx-hash", required=True, help="Hash da transação Besu.")
    args = parser.parse_args()

    tx_hash = args.tx_hash.strip().lower()
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash
    if not re.fullmatch(r"0x[0-9a-f]{64}", tx_hash):
        parser.error("--tx-hash deve conter 64 caracteres hexadecimais.")

    if not os.getenv("SUMSUB_APP_TOKEN", "").startswith("sbx:"):
        print("ERRO: configure SUMSUB_APP_TOKEN com token sbx: do Sandbox.")
        sys.exit(1)

    txn_id = "besu" + tx_hash[2:]
    # Official Sumsub GET endpoint by external txnId; sign this exact path.
    path = f"/resources/kyt/txns/-;data.txnId={quote(txn_id, safe='')}/one"
    response = sumsub_request("GET", path)
    try:
        data = response.json()
    except ValueError:
        data = {"rawText": response.text}

    print("\n=== SUMSUB TRANSACTION MONITORING RESULT ===")
    print("HTTP:", response.status_code)
    print("txnId:", txn_id)
    if response.status_code != 200:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        if response.status_code == 403:
            print("Verifique a permissão View TM transactions do App Token.")
        sys.exit(1)

    transaction_summary(data)
    print("Sumsub internal ID:", data.get("id", "N/A"))
    case_path = save_sumsub_result(tx_hash, data, stage="queried")
    print("Case atualizado:", case_path)
    print("Dashboard: Monitoring -> Transactions and activity")


if __name__ == "__main__":
    main()
