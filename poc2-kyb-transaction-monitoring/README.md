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
| NEGOCIO_RISCO_MEDIO | +5 | score |
| NEGOCIO_ALTO_RISCO | +20 | score |
| JURISDICAO_ALTO_RISCO | +25 | score |
| MIDIA_ADVERSA_EMPRESA | +25 | score |
| DOCUMENTOS_INCOMPLETOS | +30 | score |
| ORIGEM_RECURSOS_NAO_VERIFICADA | +20 | score |
| UBO_PEP | +30 | score / EDD |
| MIDIA_ADVERSA_UBO | +20 | score |
| UBO_LISTA_SANCOES | +100 | hard reject |
| REGISTRO_EMPRESA_INATIVO | +100 | hard reject |

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
NEGOCIO_RISCO_MEDIO  +5
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

## Transaction Monitoring implementado

A segunda etapa usa contexto histórico: as transações não são avaliadas isoladamente.

Parâmetros demonstrativos:

```text
Janela de estruturação:      30 minutos
Limite acumulado:            10 ETH
Janela de passagem rápida:   15 minutos
Proporção mínima de saída:   75%
```

O cenário da Fintech Delta produz:

```text
10:00  WALLET_A       -> FINTECH_DELTA      3.40 ETH
10:04  WALLET_B       -> FINTECH_DELTA      3.30 ETH
10:08  WALLET_C       -> FINTECH_DELTA      3.50 ETH
10:12  FINTECH_DELTA  -> BROKER_EPSILON     9.80 ETH
```

Regras detectadas:

| Regra | Pontos | Evidência |
| --- | ---: | --- |
| ESTRUTURACAO | +30 | três entradas abaixo de 10 ETH somam 10,20 ETH |
| PASSAGEM_RAPIDA_DE_FUNDOS | +25 | 9,80 ETH saem após o recebimento de 10,20 ETH |
| CONTRAPARTE_ALTO_RISCO | +30 | Broker Epsilon está classificado como alto risco |
| UBO_ALTO_RISCO | contexto | sinal já refletido no score corporativo |

Resultado esperado:

```text
Score corporativo:   35 / 100
Score transacional:  85 / 100
Score combinado:    100 / 100

Nível de risco:      CRÍTICO
Decisão:             ESCALAR_CASO
```

O score combinado é demonstrativo e calculado como a soma do score corporativo e do score transacional, limitada a 100. O contexto de UBO não adiciona pontos novamente para evitar dupla contagem.

### Executar a demonstração

```bash
python transaction_monitor.py
```

Para também gerar o caso consolidado:

```bash
python transaction_monitor.py --salvar
```

O arquivo será criado em:

```text
cases/monitoramento/CASO-DELTA_ESTRUTURACAO_PASSAGEM_RAPIDA.json
```

Execute todos os testes:

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
├── transaction_rules.py
├── transaction_monitor.py
├── data/
│   ├── kyb_profiles.example.json
│   ├── counterparties.example.json
│   └── transaction_scenario.example.json
└── tests/
    ├── test_kyb_rules.py
    └── test_transaction_monitor.py
```

## Próximas etapas

1. reproduzir o cenário com transações reais no Hyperledger Besu;
2. substituir os eventos JSON por leitura do histórico via JSON-RPC;
3. enriquecer o compliance case com hashes e blocos reais;
4. expor métricas de compliance para Prometheus;
5. criar dashboard de compliance no Grafana.

---

## English

This second PoC extends the original digital-asset compliance project into a more realistic AML/KYB investigation scenario.

The original PoC remains preserved. This area adds corporate KYB context, ownership and UBO risk, stateful transaction monitoring, structuring detection, rapid pass-through detection, high-risk counterparties, explainable combined risk scoring, compliance cases, and compliance observability through Prometheus and Grafana.

The core difference is that the engine no longer evaluates only one transaction in isolation. It evaluates transactions in the context of recent activity and the corporate-risk profile behind the wallet.
