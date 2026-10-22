# Digital Asset Compliance PoC

## Português

PoC de compliance para ativos digitais usando uma rede privada **Hyperledger Besu**, visualização on-chain com **Chainlens**, associação de identidade via **Sumsub Sandbox** e um mecanismo próprio de regras para gerar alertas e casos auditáveis.

> Projeto educacional e demonstrativo. Não é um sistema AML/KYT de produção.

## Objetivo

A PoC demonstra como uma instituição pode:

1. identificar uma entidade fora da blockchain;
2. associar essa entidade a uma wallet conhecida;
3. observar uma transação real em uma rede permissionada;
4. enriquecer endereços blockchain com contexto de negócio;
5. aplicar regras de risco;
6. gerar uma decisão de compliance explicável;
7. registrar o resultado em um case JSON para auditoria.

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

- Chainlens: evidência visual da atividade on-chain;
- Compliance Monitor: interpretação da transação sob a ótica de risco e compliance.

Mais detalhes em [ARCHITECTURE.md](ARCHITECTURE.md).

## Cenário principal da demonstração

A transação usada como exemplo foi registrada na rede Besu local:

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

O Compliance Monitor lê a mesma transação diretamente do Besu e gera:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW

Rule:
HIGH_VALUE_TRANSFER
Transaction amount is 10 ETH or higher
```

## Integração com Sumsub

O Banco Alpha possui um applicant de sandbox na Sumsub associado localmente à entidade da PoC.

O arquivo real `sumsub_applicants.json` é ignorado pelo Git. Para configurar o ambiente local:

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Depois substitua o placeholder pelo Applicant ID do sandbox.

Scripts auxiliares da integração Sumsub:

- `sumsub_client.py` — autenticação e assinatura das chamadas à API;
- `create_sumsub_individual.py` — criação/consulta de applicant individual no sandbox;
- `test_sumsub_env.py` — validação local das variáveis de ambiente;
- `test_sumsub_api.py` — teste de conectividade/autenticação;
- `test_sumsub_tm.py` — teste de disponibilidade do módulo Transaction Monitoring;
- `send_to_sumsub.py` — leitura de uma transação do Besu e preparação/envio do payload de Transaction Monitoring.

Para validar apenas a configuração local:

```bash
python test_sumsub_env.py
```

Para testar a API:

```bash
python test_sumsub_api.py
```

Para gerar e revisar o payload da transação de 11 ETH sem enviá-lo:

```bash
python send_to_sumsub.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c \
  --level id-only \
  --show-payload
```

Quando o script perguntar se deve enviar para a Sumsub, responda `N` se quiser apenas fazer o dry run.

### Limitação atual

A autenticação básica com a API da Sumsub foi validada no ambiente de desenvolvimento, mas o endpoint de **Transaction Monitoring/KYT** retornou:

```text
HTTP 403
"You don't have this feature enabled, please contact us"
```

Por isso, a PoC usa a Sumsub como camada de identidade e um rules engine local para a decisão de risco. Em uma implantação real, essa camada pode ser substituída ou complementada por uma plataforma especializada de transaction monitoring / blockchain intelligence.

## Regras implementadas

O `compliance_monitor.py` pode disparar:

- `HIGH_VALUE_TRANSFER`;
- `UNKNOWN_COUNTERPARTY`;
- `SENDER_KYB_NOT_APPROVED`;
- `COUNTERPARTY_KYB_NOT_APPROVED`;
- `HIGH_RISK_ENTITY`;
- `FAILED_TRANSACTION`.

Classificação atual:

```text
0–29    LOW     -> ALLOW
30–59   MEDIUM  -> REVIEW_IF_NEEDED
60–100  HIGH    -> MANUAL_REVIEW
```

O `besu_monitor.py` também demonstra análise sobre várias transações, incluindo high-value transfer e rapid pass-through.

## Estrutura do projeto

```text
poc-compliance-digital-assets/
├── README.md
├── ARCHITECTURE.md
├── besu_monitor.py
├── compliance_monitor.py
├── send_transaction.py
├── test_rpc.py
├── config.json
├── entities.json
├── wallet_intelligence.json
├── sumsub_applicants.example.json
├── sumsub_client.py
├── create_sumsub_individual.py
├── send_to_sumsub.py
├── test_sumsub_api.py
├── test_sumsub_env.py
├── test_sumsub_tm.py
├── requirements.txt
└── .gitignore
```

Arquivos gerados ou locais, como `.env`, `.venv/`, `sumsub_applicants.json`, `cases/` e `report-besu.html`, não devem ser versionados.

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

Instale as dependências:

```bash
pip install -r requirements.txt
```

Teste o RPC:

```bash
python test_rpc.py
```

Execute o monitor geral:

```bash
python besu_monitor.py --from-block 0
```

Avalie a transação principal da demonstração:

```bash
python compliance_monitor.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

O case é salvo localmente em:

```text
cases/CASE-CF85CF6D.json
```

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

## Histórico

A PoC começou com transações simuladas para validar as regras de compliance. Essa versão anterior continua preservada no histórico do Git, mas o repositório atual foi simplificado para apresentar somente a implementação baseada em Hyperledger Besu.

## Segurança

Nunca publique:

- `.env`;
- App Token ou Secret Key da Sumsub;
- private keys reais;
- wallets com fundos reais;
- credenciais de ambientes produtivos.

---

# English

This digital-asset compliance PoC uses a private **Hyperledger Besu** network, **Chainlens** for on-chain visibility, **Sumsub Sandbox** for identity association, and a local rules engine that produces explainable alerts and auditable compliance cases.

> This is an educational demonstration and not a production AML/KYT system.

## Goal

The PoC demonstrates how an institution can:

1. identify an entity off-chain;
2. associate that entity with a known wallet;
3. observe a real transaction on a permissioned blockchain;
4. enrich blockchain addresses with business context;
5. apply risk rules;
6. produce an explainable compliance decision;
7. persist the result as a JSON case for audit purposes.

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

See [ARCHITECTURE.md](ARCHITECTURE.md) for more details.

## Main demo scenario

The sample transaction was recorded on the local Besu network:

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

The Compliance Monitor reads the same transaction directly from Besu and produces:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW

Rule:
HIGH_VALUE_TRANSFER
Transaction amount is 10 ETH or higher
```

## Sumsub integration

Banco Alpha has a Sumsub sandbox applicant locally associated with the PoC entity.

The real `sumsub_applicants.json` file is ignored by Git. To configure a local environment:

```bash
cp sumsub_applicants.example.json sumsub_applicants.json
```

Then replace the placeholder with the sandbox Applicant ID.

Supporting Sumsub integration scripts:

- `sumsub_client.py` — API authentication and request signing;
- `create_sumsub_individual.py` — create/query an individual sandbox applicant;
- `test_sumsub_env.py` — validate local environment variables;
- `test_sumsub_api.py` — connectivity/authentication test;
- `test_sumsub_tm.py` — check whether Transaction Monitoring is enabled;
- `send_to_sumsub.py` — read a Besu transaction and prepare/submit the Transaction Monitoring payload.

Validate local configuration:

```bash
python test_sumsub_env.py
```

Test API connectivity:

```bash
python test_sumsub_api.py
```

Generate and inspect the 11 ETH transaction payload without submitting it:

```bash
python send_to_sumsub.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c \
  --level id-only \
  --show-payload
```

Answer `N` when prompted if you only want a dry run.

### Current limitation

Basic Sumsub API authentication was validated during development, but the **Transaction Monitoring/KYT** endpoint returned:

```text
HTTP 403
"You don't have this feature enabled, please contact us"
```

The PoC therefore uses Sumsub as the identity layer and a local rules engine for transaction-risk decisions. In a production architecture, this layer could be replaced or complemented by a specialized transaction-monitoring or blockchain-intelligence platform.

## Implemented rules

`compliance_monitor.py` can trigger:

- `HIGH_VALUE_TRANSFER`;
- `UNKNOWN_COUNTERPARTY`;
- `SENDER_KYB_NOT_APPROVED`;
- `COUNTERPARTY_KYB_NOT_APPROVED`;
- `HIGH_RISK_ENTITY`;
- `FAILED_TRANSACTION`.

Current thresholds:

```text
0–29    LOW     -> ALLOW
30–59   MEDIUM  -> REVIEW_IF_NEEDED
60–100  HIGH    -> MANUAL_REVIEW
```

`besu_monitor.py` also demonstrates analysis across multiple transactions, including high-value transfers and rapid pass-through patterns.

## Project structure

```text
poc-compliance-digital-assets/
├── README.md
├── ARCHITECTURE.md
├── besu_monitor.py
├── compliance_monitor.py
├── send_transaction.py
├── test_rpc.py
├── config.json
├── entities.json
├── wallet_intelligence.json
├── sumsub_applicants.example.json
├── requirements.txt
└── .gitignore
```

Generated or local files such as `.env`, `.venv/`, `sumsub_applicants.json`, `cases/` and `report-besu.html` must not be committed.

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

Install dependencies:

```bash
pip install -r requirements.txt
```

Test RPC:

```bash
python test_rpc.py
```

Run the general monitor:

```bash
python besu_monitor.py --from-block 0
```

Evaluate the main demo transaction:

```bash
python compliance_monitor.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

The generated case is saved under:

```text
cases/CASE-CF85CF6D.json
```

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

## History

The PoC initially used simulated transactions to validate the compliance rules. That earlier version remains available in Git history, while the current repository has been simplified to present only the Hyperledger Besu implementation.

## Security

Never publish:

- `.env`;
- Sumsub App Token or Secret Key;
- real private keys;
- wallets containing real funds;
- production credentials.
