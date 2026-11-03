import json
from urllib.request import Request, urlopen

RPC_URL = "http://localhost:8545"

def rpc(method, params=None):
    payload = json.dumps({"jsonrpc":"2.0","method":method,"params":params or [],"id":1}).encode("utf-8")
    req = Request(RPC_URL, data=payload, headers={"Content-Type":"application/json"})
    with urlopen(req, timeout=5) as response:
        body = json.loads(response.read().decode("utf-8"))
    if "error" in body:
        raise RuntimeError(body["error"])
    return body["result"]

try:
    print("OK - conectado ao Hyperledger Besu")
    print("Client:", rpc("web3_clientVersion"))
    print("Latest block:", int(rpc("eth_blockNumber"), 16))
    print("Peers:", int(rpc("net_peerCount"), 16))
except Exception as exc:
    print("ERRO - não foi possível conectar ao Besu em http://localhost:8545")
    print(exc)
