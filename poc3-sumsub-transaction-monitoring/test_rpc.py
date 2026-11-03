#!/usr/bin/env python3
"""Verify the read-only Besu JSON-RPC endpoint used by PoC 3."""
import json
import sys
from urllib.request import Request, urlopen

RPC_URL = "http://localhost:8545"


def rpc(method, params=None):
    payload = json.dumps({
        "jsonrpc": "2.0", "method": method, "params": params or [], "id": 1
    }).encode("utf-8")
    req = Request(
        RPC_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urlopen(req, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(body["error"])
    return body["result"]


def main():
    try:
        client = rpc("web3_clientVersion")
        block = int(rpc("eth_blockNumber"), 16)
        peers = int(rpc("net_peerCount"), 16)
        chain_id = int(rpc("eth_chainId"), 16)
    except Exception as exc:
        print(f"ERRO - não foi possível conectar ao Besu em {RPC_URL}")
        print(exc)
        return 1

    print("OK - conectado ao Hyperledger Besu")
    print("Client:", client)
    print("Chain ID:", chain_id)
    print("Latest block:", block)
    print("Peers:", peers)
    if chain_id != 1337:
        print("ATENÇÃO: chainId inesperado. Esperado: 1337.")
        return 1
    print("OK - rede Besu esperada (chainId 1337)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
