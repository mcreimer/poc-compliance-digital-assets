# Digital Asset Compliance PoC — Fase 2

## Português

Esta fase demonstra um fluxo de compliance para ativos digitais usando uma rede privada **Hyperledger Besu**, visualização on-chain com **Chainlens**, associação de identidade com **Sumsub** e um mecanismo próprio de regras para gerar alertas e casos auditáveis.

> Esta é uma PoC educacional. Não é um sistema AML/KYT de produção e não substitui uma solução comercial de blockchain intelligence ou transaction monitoring.

---

## Objetivo

A ideia é demonstrar como uma instituição pode:

1. identificar uma entidade fora da blockchain;
2. associar essa entidade a uma wallet conhecida;
3. observar uma transação real em uma rede privada;
4. enriquecer os endereços blockchain com contexto de negócio;
5. aplicar regras de risco;
6. gerar uma decisão de compliance explicável;
7. registrar o resultado em um caso JSON para auditoria.

---

## Arquitetura

```text
                   Sumsub
              Applicant / IDV
                     |
                     | associação de identidade
                     v
                Wallet conhecida
                     |
                     v
            Hyperledger Besu
                     |
            transação on-chain
                     |
          +----------+-----------+
          |                      |
          v                      v
      Chainlens          Compliance Monitor
   Explorer visual        regras de risco
                                 |
                                 v
                         Risk score / decisão
                                 |
                                 v
                         Compliance Case JSON
```

O **Chainlens** e o `compliance_monitor.py` observam a mesma rede Besu por perspectivas diferentes:

- Chainlens: prova visual da atividade on-chain;
- Compliance Monitor: interpretação da transação sob a ótica de risco e compliance.

---

## Cenário principal da demonstração

A transação usada como exemplo foi registrada de fato na rede Besu local:

```text
Banco Alpha
0xfe3b557e8fb62b89f4916b721be55ceb828dbd73

        | 11 ETH
        v

Custodian Gamma
0xf17f52151ebef6c7334fad080c5704d77216b732
```

Dados da transação:

```text
Block: 4453
Status: Succeeded
Tx hash:
0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

O Chainlens permite abrir essa transação e visualizar origem, destino, valor, bloco e status.

O Compliance Monitor lê a mesma transação diretamente do Besu e gera:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW

Rule:
HIGH_VALUE_TRANSFER
Transaction amount is 10 ETH or higher
```

---

## Integração com Sumsub

O Banco Alpha possui um applicant de sandbox na Sumsub associado localmente à entidade da PoC.

O arquivo real `sumsub_applicants.json` é propositalmente ignorado pelo Git para não publicar identificadores locais da conta.

Use o exemplo:

```text
sumsub_applicants.example.json
```

e crie uma cópia local:

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Depois substitua o placeholder pelo Applicant ID da sua conta sandbox.

### Limitação atual

A autenticação básica com a API da Sumsub foi validada no ambiente de desenvolvimento, mas o endpoint de **Transaction Monitoring/KYT** retornou:

```text
HTTP 403
"You don't have this feature enabled, please contact us"
```

Por isso, a PoC não depende do Transaction Monitoring da Sumsub para concluir o fluxo. A associação de identidade é demonstrada com o applicant sandbox, enquanto a decisão de risco é produzida pelo rules engine local.

Em uma implantação real, essa última camada poderia ser substituída ou complementada por Sumsub Transaction Monitoring, TRM Labs, Elliptic, Chainalysis ou outra solução especializada.

---

## Regras implementadas

O arquivo `compliance_monitor.py` avalia uma transação individual e pode disparar:

- `HIGH_VALUE_TRANSFER` — valor acima do limite configurado;
- `UNKNOWN_COUNTERPARTY` — wallet de destino não cadastrada;
- `SENDER_KYB_NOT_APPROVED` — KYB do remetente não aprovado no registry da PoC;
- `COUNTERPARTY_KYB_NOT_APPROVED` — KYB da contraparte não aprovado;
- `HIGH_RISK_ENTITY` — entidade marcada como alto risco;
- `FAILED_TRANSACTION` — transação com status de falha.

A classificação atual é:

```text
0–29    LOW     -> ALLOW
30–59   MEDIUM  -> REVIEW_IF_NEEDED
60–100  HIGH    -> MANUAL_REVIEW
```

O `besu_monitor.py` também demonstra análise comportamental sobre várias transações, incluindo high-value transfer e rapid pass-through.

---

## Estrutura da Fase 2

```text
phase2/
├── besu_monitor.py
├── compliance_monitor.py
├── config.json
├── entities.json
├── requirements-phase2.txt
├── send_transaction.py
├── sumsub_applicants.example.json
├── test_rpc.py
├── wallet_intelligence.json
└── cases/                         # gerado localmente e ignorado pelo Git
```

Arquivos locais que não devem ser versionados:

```text
.env
.venv/
sumsub_applicants.json
cases/
```

---

## Como executar

### Requisitos

- Docker Desktop
- WSL2 / Ubuntu
- Python 3
- Hyperledger Besu
- rede Besu local acessível em `http://localhost:8545`

Chain ID utilizado:

```text
1337
```

### 1. Testar o RPC

```bash
python test_rpc.py
```

### 2. Executar o monitor geral

```bash
python besu_monitor.py --from-block 0
```

Ele lê as transações diretamente da blockchain e gera `report-besu.html`.

### 3. Criar o mapeamento local da Sumsub

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Edite o arquivo local e coloque o Applicant ID real do sandbox.

### 4. Avaliar a transação de demonstração

```bash
python compliance_monitor.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

Resultado esperado:

```text
====================================
 DIGITAL ASSET COMPLIANCE ALERT
====================================

Case ID:       CASE-CF85CF6D
From:          Banco Alpha
To:            Custodian Gamma
Amount:        11.0 ETH
Block:         4453

Risk score:    60 / 100
Risk level:    HIGH
Decision:      MANUAL_REVIEW

Rules triggered:
 - HIGH_VALUE_TRANSFER: Transaction amount is 10 ETH or higher (+60)
```

O case é salvo localmente em:

```text
cases/CASE-CF85CF6D.json
```

---

## O que é real e o que é demonstrativo

### Real no ambiente da PoC

- rede privada Hyperledger Besu;
- blocos e transações reais da rede local;
- hashes e block numbers reais;
- consulta por JSON-RPC;
- visualização das transações no Chainlens;
- applicant criado na Sumsub Sandbox;
- associação entre Banco Alpha, wallet e Applicant ID;
- execução do rules engine;
- geração de compliance case em JSON.

### Demonstrativo / simplificado

- entidades Banco Alpha, Custodian Gamma etc.;
- classificação de KYB em `entities.json`;
- wallet intelligence em `wallet_intelligence.json`;
- thresholds e scores de risco;
- decisão final do rules engine.

---

## Segurança

Nunca publique:

- `.env`;
- App Token ou Secret Key da Sumsub;
- private keys reais;
- arquivos de wallet com fundos reais;
- credenciais de ambientes produtivos.

Todo o ambiente desta PoC deve usar apenas contas, wallets e ativos de teste.

---

# English

This phase demonstrates a digital-asset compliance flow using a private **Hyperledger Besu** network, **Chainlens** for on-chain visibility, **Sumsub** for identity association, and a local rules engine that produces explainable alerts and auditable compliance cases.

> This is an educational PoC. It is not a production AML/KYT system and does not replace a commercial blockchain-intelligence or transaction-monitoring platform.

---

## Goal

The PoC demonstrates how an institution can:

1. identify an entity off-chain;
2. associate that entity with a known wallet;
3. observe a real transaction on a private blockchain;
4. enrich blockchain addresses with business context;
5. apply risk rules;
6. produce an explainable compliance decision;
7. persist the result as a JSON case for audit purposes.

---

## Architecture

```text
                   Sumsub
              Applicant / IDV
                     |
                     | identity association
                     v
                Known wallet
                     |
                     v
            Hyperledger Besu
                     |
            on-chain transaction
                     |
          +----------+-----------+
          |                      |
          v                      v
      Chainlens          Compliance Monitor
   visual explorer         risk rules
                                 |
                                 v
                         Risk score / decision
                                 |
                                 v
                         Compliance Case JSON
```

Chainlens and `compliance_monitor.py` observe the same Besu network from different perspectives:

- Chainlens provides visual evidence of on-chain activity;
- Compliance Monitor interprets the transaction from a compliance and risk perspective.

---

## Main demo scenario

The sample transaction was actually recorded on the local Besu network:

```text
Banco Alpha
0xfe3b557e8fb62b89f4916b721be55ceb828dbd73

        | 11 ETH
        v

Custodian Gamma
0xf17f52151ebef6c7334fad080c5704d77216b732
```

Transaction data:

```text
Block: 4453
Status: Succeeded
Tx hash:
0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

Chainlens can be used to open the transaction and inspect sender, receiver, value, block and status.

The Compliance Monitor reads the same transaction directly from Besu and produces:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW

Rule:
HIGH_VALUE_TRANSFER
Transaction amount is 10 ETH or higher
```

---

## Sumsub integration

Banco Alpha has a sandbox applicant in Sumsub that is locally associated with the PoC entity.

The real `sumsub_applicants.json` file is intentionally ignored by Git so local account identifiers are not published.

Use:

```text
sumsub_applicants.example.json
```

and create a local copy:

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Then replace the placeholder with your sandbox Applicant ID.

### Current limitation

Basic Sumsub API authentication was validated during development, but the **Transaction Monitoring/KYT** endpoint returned:

```text
HTTP 403
"You don't have this feature enabled, please contact us"
```

For this reason, the PoC does not depend on Sumsub Transaction Monitoring to complete the demo flow. Identity association is demonstrated with the sandbox applicant, while the risk decision is generated by the local rules engine.

In a production architecture, that final layer could be replaced or complemented by Sumsub Transaction Monitoring, TRM Labs, Elliptic, Chainalysis or another specialized provider.

---

## Implemented rules

`compliance_monitor.py` evaluates one transaction and can trigger:

- `HIGH_VALUE_TRANSFER`;
- `UNKNOWN_COUNTERPARTY`;
- `SENDER_KYB_NOT_APPROVED`;
- `COUNTERPARTY_KYB_NOT_APPROVED`;
- `HIGH_RISK_ENTITY`;
- `FAILED_TRANSACTION`.

Current decision thresholds:

```text
0–29    LOW     -> ALLOW
30–59   MEDIUM  -> REVIEW_IF_NEEDED
60–100  HIGH    -> MANUAL_REVIEW
```

`besu_monitor.py` also demonstrates behavioral analysis across multiple transactions, including high-value transfers and rapid pass-through patterns.

---

## Phase 2 structure

```text
phase2/
├── besu_monitor.py
├── compliance_monitor.py
├── config.json
├── entities.json
├── requirements-phase2.txt
├── send_transaction.py
├── sumsub_applicants.example.json
├── test_rpc.py
├── wallet_intelligence.json
└── cases/                         # generated locally and ignored by Git
```

Local files that must not be versioned:

```text
.env
.venv/
sumsub_applicants.json
cases/
```

---

## How to run

Requirements:

- Docker Desktop
- WSL2 / Ubuntu
- Python 3
- Hyperledger Besu
- local Besu RPC available at `http://localhost:8545`

Chain ID:

```text
1337
```

Test RPC:

```bash
python test_rpc.py
```

Run the general monitor:

```bash
python besu_monitor.py --from-block 0
```

Create the local Sumsub mapping:

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Evaluate the demo transaction:

```bash
python compliance_monitor.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

The generated case is saved under:

```text
cases/CASE-CF85CF6D.json
```

---

## Real vs demonstrative

### Real in the PoC environment

- private Hyperledger Besu network;
- real local-chain blocks and transactions;
- real transaction hashes and block numbers;
- JSON-RPC queries;
- Chainlens transaction visualization;
- applicant created in Sumsub Sandbox;
- Banco Alpha / wallet / Applicant ID association;
- local rules-engine execution;
- JSON compliance-case generation.

### Demonstrative / simplified

- Banco Alpha, Custodian Gamma and other fictional entities;
- KYB classifications in `entities.json`;
- wallet-intelligence labels in `wallet_intelligence.json`;
- risk thresholds and scoring;
- final decision logic.

---

## Security

Never publish:

- `.env`;
- Sumsub App Token or Secret Key;
- real private keys;
- wallets containing real funds;
- production credentials.

Use test accounts, test wallets and test assets only.
