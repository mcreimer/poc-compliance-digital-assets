# Phase 2 — Hyperledger Besu

Nesta fase, a PoC deixa de ler transações simuladas de `transactions.json` e passa a ler transferências reais de uma rede privada Hyperledger Besu via JSON-RPC.

## O que agora é real
- blockchain Besu local
- blocos e hashes de transação
- endereços de origem/destino
- timestamps
- valores transferidos

## O que continua simulado
- KYB das entidades
- labels de risco de wallets
- sanctions screening
- blockchain intelligence

## Pré-requisitos
- Docker Desktop + Docker Compose v2+
- Node.js / npm
- Git Bash ou WSL no Windows
- MetaMask
- Python 3.9+

## 1. Verifique as ferramentas
```bash
docker --version
docker compose version
node --version
npm --version
python --version
```

## 2. Gere a rede Besu
Na pasta `phase2`:
```bash
npx @consensys-software/besu-dev-quickstart --networkType private --outputPath ./besu-test-network --otel false --chainlens true
```

## 3. Inicie a rede
No Git Bash ou WSL:
```bash
cd besu-test-network
./run.sh
```

Endpoints esperados:
- JSON-RPC: `http://localhost:8545`
- Chain ID: `1337`
- Chainlens: `http://localhost:8081/dashboard`

## 4. Teste a conexão
Em outro terminal, dentro de `phase2`:
```bash
python test_rpc.py
```

## 5. Configure MetaMask
Rede customizada:
- Network: `Besu Dev Quickstart`
- RPC URL: `http://localhost:8545`
- Chain ID: `1337`
- Currency: `ETH`

Mapeamento da PoC:
- Banco Alpha: `0xfe3b557e8fb62b89f4916b721be55ceb828dbd73`
- Fintech Delta: `0x627306090abaB3A6e1400e9345bC60c78a8BEf57`
- Custodian Gamma: `0xf17f52151EbEF6C7334FAD080c5704D77216b732`
- Broker Epsilon fictício: `0x1111111111111111111111111111111111111111`
- High-risk wallet fictícia: `0x2222222222222222222222222222222222222222`

Use apenas as contas de teste do Besu Developer Quickstart. Nunca use essas chaves em Mainnet.

## 6. Cenário de demonstração
1. Banco Alpha -> Custodian Gamma: 2 ETH (normal)
2. Banco Alpha -> Fintech Delta: 12 ETH (high value)
3. Em até 15 min, Fintech Delta -> Custodian Gamma: 11 ETH (rapid pass-through)
4. Uma conta de teste -> `0x2222...2222`: 6 ETH (high-risk wallet)
5. Banco Alpha -> `0x1111...1111`: 1 ETH (KYB pending + sanctions mock)

## 7. Rode o monitor
```bash
python besu_monitor.py
```

O script lê os blocos via JSON-RPC e gera `report-besu.html`.

A próxima evolução natural é trocar ETH por uma stablecoin ERC-20 fictícia (por exemplo BRLx), mantendo o mesmo motor de compliance.
