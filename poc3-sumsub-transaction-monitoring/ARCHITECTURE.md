# Arquitetura — PoC 3 (Sumsub Transaction Monitoring Sandbox)

## Fronteiras e isolamento

- Código da PoC 3 isolado em `poc3-sumsub-transaction-monitoring/`, branch `poc3-sumsub-transaction-monitoring`.
- PoC 1: scripts na raiz do repositório, mantidos intocados nesta branch.
- PoC 2: pasta `poc2-kyb-transaction-monitoring/`, mantida intocada nesta branch.
- Ambiente Linux recomendado: clone separado em `~/poc3-sumsub-tm/`.
- Segredos e case output localizados e ignorados pelo Git.
- O Besu é lido pelo RPC `http://localhost:8545`; **nenhuma escrita ou deploy on-chain** pela PoC 3.

## Fluxos

1. **Conectividade** — `test_rpc.py` e `test_sumsub_tm.py`.
2. **Captura** — `send_to_sumsub.py` chama `eth_getTransactionByHash`, `eth_getBlockByNumber`, `eth_getTransactionReceipt`.
3. **Payload** — transação financeira (ETH), identificadores de carteiras, timestamp, identidade fictícia do Banco Alpha e Custodian Gamma. Campos internos incluem `chainId: 1337`.
4. **Envio** — POST `/resources/applicants/{applicantId}/kyt/txns/-/data`, com assinatura HMAC SHA-256 e token Sandbox. `txnId = besu<hash_sem_0x>` para deduplicação.
5. **Consulta** — GET `/resources/kyt/txns/-;data.txnId={txnId}/one`.
6. **Evidências** — `cases/CASE-CF85CF6D.json` recebe a resposta da API em `sumsubTransactionMonitoring`, sem mudar `riskAssessment` local.

## Limitações
O transaction monitoring de negócio pode analisar o payload enviado; isto não equivale a verificação independente da transferência na blockchain pública. Screening criptográfico e provedores externos podem não reconhecer o endereço/txHash da chain privada. O motor local é demonstrativo e não serve para decisões reais de compliance.
