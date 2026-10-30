# Architecture — KYB & Transaction Monitoring PoC

## Objetivo

Combinar risco corporativo e comportamento transacional em uma decisão única e explicável.

## Fluxo

```text
Company / KYB Profile
        |
        +--> Ownership structure
        |
        +--> UBO screening
        |
        +--> Corporate risk
        |
        v
Known corporate wallet
        |
        v
Hyperledger Besu
        |
        v
Transaction history
        |
        v
Stateful Transaction Monitor
        |
        +--> Structuring detection
        +--> Velocity detection
        +--> Rapid pass-through
        +--> High-risk counterparty
        +--> UBO / corporate-risk enrichment
        |
        v
Combined risk score
        |
        +--> ALLOW
        +--> REVIEW
        +--> ESCALATE_CASE
        |
        v
Compliance Case JSON
        |
        +--> Prometheus metrics
                |
                v
             Grafana
```

## Separação de riscos

### Corporate Risk

Derivado de dados de KYB, por exemplo:

- status cadastral;
- jurisdição;
- atividade econômica;
- estrutura societária;
- UBOs;
- PEP/sanctions/adverse-media flags simulados;
- status de enhanced due diligence.

### Transaction Risk

Derivado do comportamento on-chain, por exemplo:

- volume acumulado em uma janela;
- número de entradas e saídas;
- structuring;
- rapid pass-through;
- destino de alto risco;
- velocidade transacional;
- falha ou anomalia da transação.

## Princípio de explicabilidade

Todo score deve registrar:

- regra;
- evidência;
- contribuição para o score;
- entidade afetada;
- transações relacionadas;
- janela temporal utilizada.

A decisão final nunca deve depender apenas de um número sem contexto.
