#!/usr/bin/env python3
"""
send_to_sumsub.py

Reads an existing transaction from a local Hyperledger Besu network and
submits it to Sumsub Transaction Monitoring Sandbox.

IMPORTANT:
- This PoC uses an individual applicant as a sandbox surrogate because the
  current Sumsub account does not have company/KYB verification enabled.
- The Besu network is private (chainId 1337). Sumsub can monitor the submitted
  transaction data/rules, but external blockchain analytics providers cannot
  independently find this private-chain transaction on public Ethereum.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

from sumsub_client import request as sumsub_request


BASE = Path(__file__).resolve().parent
DEFAULT_RPC_URL = "http://localhost:8545"

DEFAULT_ENTITIES = {
    "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73": {
        "id": "BANK_ALPHA",
        "name": "Banco Alpha",
        "demo_person": "Test User Alpha",
    },
    "0x627306090abab3a6e1400e9345bc60c78a8bef57": {
        "id": "FINTECH_DELTA",
        "name": "Fintech Delta",
        "demo_person": "Test User Delta",
    },
    "0xf17f52151ebef6c7334fad080c5704d77216b732": {
        "id": "CUSTODIAN_GAMMA",
        "name": "Custodian Gamma",
        "demo_person": "Test User Gamma",
    },
}


def rpc_call(rpc_url, method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }
    response = requests.post(rpc_url, json=payload, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data["result"]


def load_entities():
    entities = dict(DEFAULT_ENTITIES)
    path = BASE / "entities.json"

    if not path.exists():
        return entities

    try:
        with path.open("r", encoding="utf-8") as f:
            rows = json.load(f)

        for row in rows:
            wallet = row.get("wallet")
            if not wallet:
                continue

            wallet = wallet.lower()
            entity_id = row.get("id", f"WALLET_{wallet[-8:].upper()}")
            name = row.get("name", entity_id)

            entities[wallet] = {
                "id": entity_id,
                "name": name,
                "demo_person": f"Test User {name}",
            }
    except Exception as exc:
        print(f"ATENÇÃO: não foi possível ler entities.json: {exc}")

    return entities


def entity_for(address, entities):
    address = address.lower()

    if address in entities:
        return entities[address]

    return {
        "id": f"UNKNOWN_{address[-8:].upper()}",
        "name": f"Unknown Wallet {address[:10]}...",
        "demo_person": "Test User Counterparty",
    }


def get_besu_transaction(rpc_url, tx_hash):
    tx = rpc_call(rpc_url, "eth_getTransactionByHash", [tx_hash])

    if tx is None:
        raise RuntimeError(f"Transação não encontrada no Besu: {tx_hash}")

    if not tx.get("blockNumber"):
        raise RuntimeError("A transação ainda não foi incluída em um bloco.")

    block = rpc_call(rpc_url, "eth_getBlockByNumber", [tx["blockNumber"], False])

    if block is None:
        raise RuntimeError(f"Bloco {tx['blockNumber']} não encontrado.")

    receipt = rpc_call(rpc_url, "eth_getTransactionReceipt", [tx_hash])

    return tx, block, receipt


def to_txn_date(timestamp_hex):
    timestamp = int(timestamp_hex, 16)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S+0000")


def build_sumsub_payload(tx, block, receipt, entities):
    sender = tx["from"].lower()
    recipient = tx["to"].lower() if tx.get("to") else None

    if not recipient:
        raise RuntimeError("Esta versão da PoC não envia contract creation para Sumsub.")

    sender_entity = entity_for(sender, entities)
    recipient_entity = entity_for(recipient, entities)

    amount_eth = int(tx["value"], 16) / 10**18
    block_number = int(tx["blockNumber"], 16)
    tx_hash = tx["hash"]

    txn_id = "besu" + tx_hash.lower().replace("0x", "")

    payload = {
        "txnId": txn_id,
        "txnDate": to_txn_date(block["timestamp"]),
        "zoneId": "UTC+00:00",
        "type": "finance",
        "info": {
            "direction": "out",
            "amount": amount_eth,
            "currencyCode": "ETH",
            "currencyType": "crypto",
            "paymentDetails": "Hyperledger Besu private-network PoC transfer",
            "paymentTxnId": tx_hash,
            "type": "besu-private-transfer",
        },
        "applicant": {
            "type": "individual",
            "externalUserId": f"POC_{sender_entity['id']}",
            "fullName": sender_entity["demo_person"],
            "institutionInfo": {
                "address": {"country": "BRA"},
                "name": f"{sender_entity['name']} PoC",
            },
            "paymentMethod": {
                "type": "crypto",
                "accountId": sender,
            },
        },
        "counterparty": {
            "type": "individual",
            "externalUserId": f"POC_{recipient_entity['id']}",
            "fullName": recipient_entity["demo_person"],
            "institutionInfo": {
                "address": {"country": "BRA"},
                "name": f"{recipient_entity['name']} PoC",
            },
            "paymentMethod": {
                "type": "crypto",
                "accountId": recipient,
            },
        },
        "props": {
            "network": "Hyperledger Besu Private",
            "chainId": "1337",
            "blockNumber": str(block_number),
            "blockHash": block["hash"],
            "besuTxHash": tx_hash,
            "fromEntity": sender_entity["id"],
            "toEntity": recipient_entity["id"],
            "receiptStatus": str(int(receipt["status"], 16)) if receipt else "",
            "localPrivateNetwork": "true",
        },
    }

    return payload, sender_entity, recipient_entity, amount_eth, block_number


def main():
    parser = argparse.ArgumentParser(
        description="Envia uma transação Besu já confirmada ao Sumsub Transaction Monitoring Sandbox."
    )

    parser.add_argument(
        "--tx-hash",
        required=True,
        help="Hash da transação existente no Hyperledger Besu.",
    )

    parser.add_argument(
        "--level",
        required=True,
        help="Nome EXATO de um nível de verificação de pessoa física no Sumsub Sandbox.",
    )

    parser.add_argument(
        "--rpc",
        default=DEFAULT_RPC_URL,
        help=f"Besu JSON-RPC URL (default: {DEFAULT_RPC_URL})",
    )

    parser.add_argument(
        "--show-payload",
        action="store_true",
        help="Mostra o JSON que será enviado à Sumsub (sem credenciais).",
    )

    args = parser.parse_args()

    tx_hash = args.tx_hash.strip()
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash

    print("\n=== BESU -> SUMSUB TRANSACTION MONITORING ===")
    print("Besu RPC:", args.rpc)
    print("Sumsub level:", args.level)
    print("Tx hash:", tx_hash)

    try:
        entities = load_entities()
        tx, block, receipt = get_besu_transaction(args.rpc, tx_hash)

        payload, sender_entity, recipient_entity, amount_eth, block_number = (
            build_sumsub_payload(tx, block, receipt, entities)
        )
    except Exception as exc:
        print("\nERRO ao ler a transação do Besu:")
        print(exc)
        sys.exit(1)

    print("\nTransação encontrada no Besu:")
    print("Block:", block_number)
    print("From:", tx["from"], f"({sender_entity['name']})")
    print("To:  ", tx["to"], f"({recipient_entity['name']})")
    print("Value:", amount_eth, "ETH")
    print("Receipt status:", int(receipt["status"], 16) if receipt else "N/A")

    if args.show_payload:
        print("\nPayload a enviar para Sumsub:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))

    answer = input("\nEnviar esta transação ao Sumsub Sandbox? [y/N]: ").strip().lower()

    if answer != "y":
        print("Operação cancelada.")
        return

    path = (
        "/resources/applicants/-/kyt/txns/-/data"
        f"?levelName={quote(args.level, safe='')}"
    )
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)

    print("\nEnviando para Sumsub...")

    response = sumsub_request("POST", path, body)

    print("HTTP status:", response.status_code)

    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        data = None
        print(response.text)

    if response.status_code == 409:
        print(
            "\nA Sumsub informou que esse txnId já existe. "
            "Isso é esperado se você já tiver enviado essa mesma transação."
        )
        return

    if response.status_code != 200:
        print("\nERRO: a transação não foi aceita pelo Sumsub.")
        print(
            "Confira principalmente o nome do level, permissões do App Token "
            "e se Transaction Monitoring está habilitado no Sandbox."
        )
        sys.exit(1)

    print("\n=== TRANSACTION SUBMITTED ===")
    print("Sumsub txnId:", payload["txnId"])
    print("Besu tx hash:", tx_hash)
    print("Block:", block_number)
    print(
        "\nAgora abra no Dashboard Sumsub: "
        "Transações e Travel Rule -> Transações, e procure pelo txnId."
    )
    print(
        "\nObservação: como esta é uma rede Besu privada (chainId 1337), "
        "provedores externos de blockchain analytics não conseguirão localizar "
        "esse hash na Ethereum pública. O objetivo desta etapa é testar "
        "Transaction Monitoring e regras da Sumsub."
    )


if __name__ == "__main__":
    main()
