#!/usr/bin/env python3
"""Read-only by default; optionally review a Sumsub TM Sandbox transaction.

Do not run a final decision before capturing the onHold stage for the demo.
Only a consciously confirmed --decision performs a POST to Sumsub.
"""
import argparse
import json
import os
import re
import sys
from urllib.parse import quote

from sumsub_client import request as sumsub_request
from sumsub_tm_case import save_sumsub_result, transaction_summary


def fetch_by_external_id(txn_id):
    path = f"/resources/kyt/txns/-;data.txnId={quote(txn_id, safe='')}/one"
    response = sumsub_request("GET", path)
    if response.status_code != 200:
        raise RuntimeError(
            f"GET Sumsub returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )
    return response.json()


def check_sandbox():
    if not os.getenv("SUMSUB_APP_TOKEN", "").startswith("sbx:"):
        raise RuntimeError("Apenas SUMSUB_APP_TOKEN do Sandbox (sbx:) é aceito.")


def validate_decision(target, transaction, explicit_id, decision):
    """Preflight: fail closed before any write request."""
    if transaction.get("id") != explicit_id:
        raise ValueError(
            "ID da transação Sumsub não corresponde ao ID confirmado. "
            "A operação foi cancelada."
        )
    if not re.fullmatch(r"[A-Za-z0-9]{12,64}", explicit_id):
        raise ValueError("ID interno da Sumsub inválido.")
    state = (transaction.get("review") or {}).get("reviewStatus")
    if state != "onHold":
        raise ValueError(
            f"Esperado reviewStatus=onHold; recebido {state!r}. "
            "Não é seguro enviar uma decisão."
        )
    txn_id = (transaction.get("data") or {}).get("txnId")
    if txn_id != target:
        raise ValueError("txnId da resposta não corresponde ao esperado.")
    if decision not in ("approve", "reject"):
        raise ValueError("Apenas approve/reject são suportados.")


def decide_internal_transaction(sumsub_id, decision):
    # Official TM transaction decision API; NOT applicant KYC approval.
    path = f"/resources/kyt/txns/{quote(sumsub_id, safe='')}/review/status/completed"
    answer = "GREEN" if decision == "approve" else "RED"
    body = json.dumps({"reviewAnswer": answer}, separators=(",", ":"))
    response = sumsub_request("POST", path, body)
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"POST decision returned HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )
    return response.json()


def main():
    p = argparse.ArgumentParser(
        description="Inspeciona o alerta no Sandbox e opcionalmente decide manualmente."
    )
    p.add_argument("--tx-hash", required=True, help="Besu transaction hash")
    p.add_argument(
        "--decision", choices=["approve", "reject"], default=None,
        help="Uma alteração REAL no Sandbox: não use antes de gravar o onHold."
    )
    p.add_argument(
        "--confirm-sumsub-id", default=None,
        help="ID interno da Sumsub. Obrigatório ao passar --decision."
    )
    args = p.parse_args()

    tx_hash = args.tx_hash.lower().strip()
    if not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash
    if not re.fullmatch(r"0x[0-9a-f]{64}", tx_hash):
        p.error("tx-hash precisa ter 64 caracteres hexadecimais.")
    if args.confirm_sumsub_id and not args.decision:
        p.error("--confirm-sumsub-id deve ser usado junto com --decision")
    if args.decision and not args.confirm_sumsub_id:
        p.error("--confirm-sumsub-id é obrigatório ao tomar uma decisão.")

    try:
        check_sandbox()
        external_id = "besu" + tx_hash[2:]
        transaction = fetch_by_external_id(external_id)
        print("\n=== SUMSUB TM SANDBOX | MANUAL REVIEW ===")
        print("External txnId:", external_id)
        print("Sumsub internal ID:", transaction.get("id"))
        transaction_summary(transaction)
        saved = save_sumsub_result(tx_hash, transaction, stage="review-inspected")
        print("Evidência consultada e salva:", saved)

        if not args.decision:
            print("\nMODO SOMENTE CONSULTA — nenhuma decisão foi enviada.")
            print("Para o vídeo, abra Sumsub > Monitoramento de transações > "
                  "Transações, atribua o analista e adicione a nota.")
            return 0

        validate_decision(
            external_id, transaction, args.confirm_sumsub_id, args.decision
        )
        print("\nATENÇÃO: esta operação irá encerrar a revisão no SANDBOX.")
        print("Decisão:", args.decision.upper())
        print("Sumsub ID:", args.confirm_sumsub_id)
        challenge = f"CONFIRM {args.decision.upper()} {args.confirm_sumsub_id}"
        user_input = input(f"Para continuar, digite exatamente: {challenge}\n> ")
        if user_input != challenge:
            print("Decisão cancelada; estado da transação preservado.")
            return 0

        # Explicit double confirmation provided; perform one provider write.
        result = decide_internal_transaction(args.confirm_sumsub_id, args.decision)
        print("\nPOST aceito pela Sumsub. Consultando status final...")
        if result.get("id") and result["id"] != args.confirm_sumsub_id:
            raise RuntimeError("A resposta POST referencia outra transação.")
        latest = fetch_by_external_id(external_id)
        transaction_summary(latest)
        path = save_sumsub_result(
            tx_hash, latest, stage="manual-decision-confirmed"
        )
        print("Case e linha do tempo atualizados:", path)
        print("Veja a decisão e os eventos no dashboard Sumsub.")
        return 0
    except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print("ERRO:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
