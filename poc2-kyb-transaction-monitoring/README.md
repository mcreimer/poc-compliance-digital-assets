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

## Modelo KYB implementado

O perfil corporativo agora é avaliado por um engine determinístico. O JSON de entrada contém fatos e flags; `kyb_rules.py` calcula o score, o nível de risco e o status.

### Validações

- entidade deve ser do tipo `company`;
- wallet deve ter formato Ethereum;
- deve existir pelo menos um UBO;
- IDs de UBO não podem se repetir;
- percentuais de ownership precisam totalizar 100%.

### Regras demonstrativas

| Regra | Pontos | Efeito |
| --- | ---: | --- |
| MEDIUM_RISK_BUSINESS | +5 | score |
| HIGH_RISK_BUSINESS | +20 | score |
| HIGH_RISK_JURISDICTION | +25 | score |
| COMPANY_ADVERSE_MEDIA | +25 | score |
| DOCUMENTS_INCOMPLETE | +30 | score |
| SOURCE_OF_FUNDS_UNVERIFIED | +20 | score |
| UBO_PEP | +30 | score / EDD |
| UBO_ADVERSE_MEDIA | +20 | score |
| UBO_SANCTIONS_MATCH | +100 | hard reject |
| REGISTRATION_NOT_ACTIVE | +100 | hard reject |

Classificação:

```text
0-9     LOW       -> APPROVED
10-29   MEDIUM    -> APPROVED
30-69   HIGH      -> EDD_REQUIRED
70-100  CRITICAL  -> REJECTED
```

Um hard reject sempre resulta em `REJECTED`.

> Os pesos e thresholds são exclusivamente demonstrativos e não representam requisitos regulatórios.

Para a Fintech Delta, o resultado esperado é:

```text
MEDIUM_RISK_BUSINESS  +5
UBO_PEP              +30
-------------------------
Corporate Risk        35 / 100
Risk Level            HIGH
KYB Status            EDD_REQUIRED
```

## Como executar o KYB

Entre na pasta:

```bash
cd poc2-kyb-transaction-monitoring
```

Avalie a Fintech Delta:

```bash
python evaluate_kyb.py --entity FINTECH_DELTA
```

Para também salvar o assessment em JSON:

```bash
python evaluate_kyb.py --entity FINTECH_DELTA --save
```

O resultado será criado em:

```text
cases/kyb/KYB-FINTECH_DELTA.json
```

Execute os testes:

```bash
python -m unittest discover -s tests -v
```

## Estrutura atual

```text
poc2-kyb-transaction-monitoring/
├── README.md
├── ARCHITECTURE.md
├── kyb_model.py
├── kyb_rules.py
├── evaluate_kyb.py
├── data/
│   ├── kyb_profiles.example.json
│   └── transaction_scenario.example.json
└── tests/
    └── test_kyb_rules.py
```

## Próximas etapas

1. criar as transações do cenário no Besu;
2. implementar `transaction_monitor.py` com janelas temporais;
3. combinar corporate risk e transaction risk;
4. gerar compliance case enriquecido;
5. expor métricas de compliance;
6. criar dashboard no Grafana.

---

## English

This second PoC extends the original digital-asset compliance project into a more realistic AML/KYB investigation scenario.

The original PoC remains preserved. This area adds corporate KYB context, ownership and UBO risk, stateful transaction monitoring, structuring detection, rapid pass-through detection, high-risk counterparties, explainable combined risk scoring, compliance cases, and compliance observability through Prometheus and Grafana.

The core difference is that the engine no longer evaluates only one transaction in isolation. It evaluates transactions in the context of recent activity and the corporate-risk profile behind the wallet.
