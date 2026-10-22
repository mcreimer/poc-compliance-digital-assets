#!/usr/bin/env python3
"""
send_transaction.py
Digital Asset Compliance PoC

Signs a native ETH transfer locally and sends it to a Hyperledger Besu
private network through JSON-RPC.

IMPORTANT:
- Use only development/test private keys.
- Never use a real wallet private key with this PoC.
"""

import argparse
import getpass
import os
import sys

from web3 import Web3
from eth_account import Account


DEFAULT_RPC_URL = "http://localhost:8545"
DEFAULT_CHAIN_ID = 1337
DEFAULT_RECIPIENT = "0xf17f52151EbEF6C7334FAD080c5704D77216b732"  # Custodian Gamma
EXPECTED_BANK_ALPHA = "0xfe3b557e8fb62b89f4916b721be55ceb828dbd73"


def get_private_key():
    """
    Read the private key from BESU_PRIVATE_KEY.
    If it is not defined, ask interactively without echoing it on screen.
    """
    key = os.getenv("BESU_PRIVATE_KEY")

    if not key:
        key = getpass.getpass(
            "Private key da conta de teste (não será exibida): "
        ).strip()

    if not key:
        raise ValueError("Nenhuma private key foi informada.")

    if not key.startswith("0x"):
        key = "0x" + key

    return key


def main():
    parser = argparse.ArgumentParser(
        description="Envia uma transferência ETH de teste para uma rede Hyperledger Besu."
    )
    parser.add_argument(
        "--rpc",
        default=DEFAULT_RPC_URL,
        help=f"Besu JSON-RPC URL (default: {DEFAULT_RPC_URL})",
    )
    parser.add_argument(
        "--to",
        default=DEFAULT_RECIPIENT,
        help=f"Endereço destinatário (default: Custodian Gamma {DEFAULT_RECIPIENT})",
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=2.0,
        help="Quantidade de ETH de teste a enviar (default: 2)",
    )
    parser.add_argument(
        "--chain-id",
        type=int,
        default=DEFAULT_CHAIN_ID,
        help=f"Chain ID (default: {DEFAULT_CHAIN_ID})",
    )
    args = parser.parse_args()

    print("\n=== BESU TEST TRANSACTION ===")
    print(f"RPC:      {args.rpc}")
    print(f"Chain ID: {args.chain_id}")
    print(f"To:       {args.to}")
    print(f"Amount:   {args.amount} ETH\n")

    w3 = Web3(Web3.HTTPProvider(args.rpc, request_kwargs={"timeout": 10}))

    if not w3.is_connected():
        print(f"ERRO: não foi possível conectar ao Besu em {args.rpc}")
        sys.exit(1)

    actual_chain_id = w3.eth.chain_id
    print(f"Besu chain ID detectado: {actual_chain_id}")

    if actual_chain_id != args.chain_id:
        print(
            f"ERRO: chain ID esperado {args.chain_id}, "
            f"mas o Besu retornou {actual_chain_id}."
        )
        sys.exit(1)

    try:
        private_key = get_private_key()
        account = Account.from_key(private_key)
    except Exception as exc:
        print(f"ERRO ao carregar private key: {exc}")
        sys.exit(1)

    sender = Web3.to_checksum_address(account.address)
    recipient = Web3.to_checksum_address(args.to)

    print(f"From:     {sender}")

    if sender.lower() != EXPECTED_BANK_ALPHA.lower():
        print(
            "\nATENÇÃO: a chave informada não corresponde ao Banco Alpha esperado:"
        )
        print(EXPECTED_BANK_ALPHA)
        answer = input("Deseja continuar mesmo assim? [y/N]: ").strip().lower()
        if answer != "y":
            print("Operação cancelada.")
            sys.exit(0)

    balance_before = w3.eth.get_balance(sender)
    balance_eth = w3.from_wei(balance_before, "ether")

    print(f"Balance:  {balance_eth} ETH")

    value_wei = w3.to_wei(args.amount, "ether")

    if balance_before < value_wei:
        print("ERRO: saldo insuficiente para a transferência.")
        sys.exit(1)

    nonce = w3.eth.get_transaction_count(sender, "pending")

    # Legacy transaction is intentionally used for maximum compatibility
    # with Besu private development networks.
    gas_price = w3.eth.gas_price

    transaction = {
        "nonce": nonce,
        "to": recipient,
        "value": value_wei,
        "gas": 21000,
        "gasPrice": gas_price,
        "chainId": args.chain_id,
    }

    print("\nTransaction parameters:")
    print(f"  Nonce:     {nonce}")
    print(f"  Gas:       {transaction['gas']}")
    print(f"  Gas price: {gas_price} wei")

    signed = account.sign_transaction(transaction)

    try:
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    except AttributeError:
        # Compatibility with older eth-account/web3 versions
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

    tx_hash_hex = tx_hash.hex()

    print("\nTransação enviada.")
    print(f"Tx hash: {tx_hash_hex}")
    print("Aguardando confirmação...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    print("\n=== CONFIRMED ===")
    print(f"Status:      {receipt.status}")
    print(f"Block:       {receipt.blockNumber}")
    print(f"Gas used:    {receipt.gasUsed}")
    print(f"Tx hash:     {tx_hash_hex}")

    balance_after = w3.eth.get_balance(sender)
    print(f"New balance: {w3.from_wei(balance_after, 'ether')} ETH")

    if receipt.status != 1:
        print("\nATENÇÃO: a transação foi incluída, mas falhou.")
        sys.exit(2)

    print("\nPróximo passo:")
    print("  python3 besu_monitor.py")


if __name__ == "__main__":
    main()
