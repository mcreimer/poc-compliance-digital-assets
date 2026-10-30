# PoC 2 — KYB & Transaction Monitoring

## Português

Esta segunda PoC evolui o projeto original de compliance de ativos digitais para um cenário mais próximo de uma investigação AML/KYB real.

A PoC original permanece preservada. Esta área adiciona uma camada separada de:

- perfil corporativo KYB;
- estrutura societária e UBOs;
- risco corporativo;
- comportamento transacional com contexto histórico;
- detecção de structuring;
- rapid pass-through;
- contraparte de alto risco;
- combinação entre risco da empresa e risco da transação;
- geração de caso;
- métricas de compliance para Prometheus;
- dashboard de compliance no Grafana.

> Projeto educacional e demonstrativo. Não é um sistema AML/KYT de produção.

## Cenário principal

A entidade central será a **Fintech Delta**.

Exemplo inicial de perfil:

```text
FINTECH DELTA LTDA.
|
+-- UBO 1 - 70%
|   +-- Risk: LOW
|
+-- UBO 2 - 30%
    +-- PEP match: YES
    +-- Risk: HIGH

Corporate status: EDD_REQUIRED
```

A empresa recebe várias transferências em uma janela curta:

```text
10:00  Wallet A -> Fintech Delta    3.4 ETH
10:04  Wallet B -> Fintech Delta    3.3 ETH
10:08  Wallet C -> Fintech Delta    3.5 ETH

Total recebido: 10.2 ETH
```

Pouco depois:

```text
10:12  Fintech Delta -> Broker Epsilon    9.8 ETH
```

O objetivo é detectar a combinação de sinais:

- STRUCTURING;
- RAPID_PASS_THROUGH;
- HIGH_RISK_COUNTERPARTY;
- HIGH_RISK_UBO.

Resultado esperado:

```text
Transaction Risk Score: 100 / 100
Risk Level: CRITICAL
Decision: ESCALATE_CASE
```

## Evolução em relação à primeira PoC

A primeira PoC responde principalmente:

> "Esta transação individual viola alguma regra?"

Esta segunda PoC passa a responder:

> "Esta transação, considerando o histórico recente, o perfil KYB da empresa, seus UBOs e o risco das contrapartes, é suspeita?"

## Componentes planejados

```text
KYB / Company Profile
        |
Ownership / UBOs
        |
Corporate Risk
        |
        v
Hyperledger Besu
        |
Transaction History
        |
        v
Stateful Transaction Monitor
        |
 +------+------+------+------+
 |      |      |      |      |
 v      v      v      v      v
Struct. Velocity Pass-through Counterparty UBO Risk
        |
        v
Combined Risk
        |
        v
Compliance Case
        |
 +------+------+
 |             |
 v             v
JSON       Prometheus
               |
               v
            Grafana
```

## Estrutura inicial

```text
poc2-kyb-transaction-monitoring/
├── README.md
├── ARCHITECTURE.md
└── data/
    ├── kyb_profiles.example.json
    └── transaction_scenario.example.json
```

Os próximos componentes serão adicionados nesta pasta, sem modificar a implementação da PoC original.

## Próximas etapas

1. modelar KYB, ownership e UBO risk;
2. criar transações do cenário no Besu;
3. implementar `transaction_monitor.py` com janelas temporais;
4. combinar corporate risk e transaction risk;
5. gerar compliance case enriquecido;
6. expor métricas de compliance;
7. criar dashboard no Grafana.

---

## English

This second PoC extends the original digital-asset compliance project into a more realistic AML/KYB investigation scenario.

The original PoC remains preserved. This area adds corporate KYB context, ownership and UBO risk, stateful transaction monitoring, structuring detection, rapid pass-through detection, high-risk counterparties, explainable combined risk scoring, compliance cases, and compliance observability through Prometheus and Grafana.

The core difference is that the engine no longer evaluates only one transaction in isolation. It evaluates transactions in the context of recent activity and the corporate-risk profile behind the wallet.
