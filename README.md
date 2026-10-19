# Digital Asset Compliance PoC

## Português

PoC de compliance para ativos digitais que evolui de transações simuladas para uma rede privada **Hyperledger Besu** com visualização em **Chainlens**, associação de identidade via **Sumsub Sandbox** e geração de alertas/casos de compliance por regras explicáveis.

> Projeto educacional e demonstrativo. Não é um sistema AML/KYT de produção.

## O que a PoC demonstra

O fluxo atual é:

```text
Identidade / Applicant
        |
        v
   Wallet conhecida
        |
        v
 Hyperledger Besu
        |
        +--> Chainlens
        |    visualização on-chain
        |
        +--> Compliance Monitor
             regras de risco
                  |
                  v
          Risk score / decisão
                  |
                  v
          Compliance Case JSON
```

A transação principal usada na demonstração é uma transferência real da rede local:

```text
Banco Alpha -> Custodian Gamma
11 ETH
Block 4453
Status: Succeeded
```

O rules engine classifica essa transação como:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW
Rule: HIGH_VALUE_TRANSFER
```

## Fases

### Fase 1

Validação inicial da lógica de compliance com transações simuladas.

Inclui:

- KYB fictício;
- high-value transfer;
- rapid pass-through;
- mock wallet intelligence;
- sanctions indicators simulados;
- scoring explicável;
- relatório HTML.

### Fase 2

Integração com uma rede privada Hyperledger Besu.

Inclui:

- transações reais da rede local;
- consulta via JSON-RPC;
- visualização com Chainlens;
- associação entre entidades e wallets;
- applicant sandbox da Sumsub associado ao Banco Alpha;
- monitoramento por regras;
- geração de compliance case em JSON.

A documentação detalhada está em:

[phase2/README.md](phase2/README.md)

## Sumsub

A PoC usa um applicant sandbox para demonstrar a associação entre identidade e wallet.

O módulo **Transaction Monitoring/KYT** não foi habilitado para a conta sandbox utilizada no desenvolvimento. Por isso, a PoC mantém a camada de identidade da Sumsub e usa um rules engine local para produzir o alerta de transação.

## Segurança

Credenciais, arquivos `.env`, private keys reais e o arquivo local `sumsub_applicants.json` não devem ser versionados.

---

# English

This digital-asset compliance PoC evolves from simulated transactions to a private **Hyperledger Besu** network with **Chainlens** on-chain visibility, **Sumsub Sandbox** identity association, and an explainable local compliance rules engine.

> This is an educational demonstration and not a production AML/KYT system.

## What the PoC demonstrates

Current flow:

```text
Identity / Applicant
        |
        v
    Known wallet
        |
        v
 Hyperledger Besu
        |
        +--> Chainlens
        |    on-chain visibility
        |
        +--> Compliance Monitor
             risk rules
                  |
                  v
          Risk score / decision
                  |
                  v
          Compliance Case JSON
```

Main demo transaction:

```text
Banco Alpha -> Custodian Gamma
11 ETH
Block 4453
Status: Succeeded
```

Rules-engine result:

```text
Risk score: 60 / 100
Risk level: HIGH
Decision: MANUAL_REVIEW
Rule: HIGH_VALUE_TRANSFER
```

## Phases

### Phase 1

Initial validation using simulated transactions, KYB data, wallet-risk indicators, sanctions signals, rapid pass-through detection and explainable risk scoring.

### Phase 2

Integration with a private Hyperledger Besu network, JSON-RPC transaction retrieval, Chainlens visualization, entity-to-wallet mapping, Sumsub sandbox applicant association, transaction rules and JSON compliance-case generation.

Detailed documentation:

[phase2/README.md](phase2/README.md)

## Sumsub

The PoC uses a sandbox applicant to demonstrate identity-to-wallet association.

The **Transaction Monitoring/KYT** feature was not enabled for the sandbox account used during development. The PoC therefore keeps Sumsub as the identity layer and uses a local rules engine for transaction-risk decisions.

## Security

Do not commit credentials, `.env` files, real private keys or the local `sumsub_applicants.json` mapping.
