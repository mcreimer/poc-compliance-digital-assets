# Arquitetura / Architecture

## Português

A PoC foi construída para separar claramente quatro responsabilidades:

1. **Identidade** — associação entre uma entidade e um applicant sandbox;
2. **Blockchain** — execução e persistência da transação em Hyperledger Besu;
3. **Observabilidade** — inspeção visual da rede e das transações no Chainlens;
4. **Compliance** — enriquecimento das wallets, aplicação de regras e geração de um case auditável.

```text
                        +------------------+
                        |      Sumsub      |
                        | Applicant / IDV  |
                        +---------+--------+
                                  |
                                  | identidade / contexto
                                  v
+----------------+        +------------------+
|  Banco Alpha   |------->|  Known Wallet    |
+----------------+        +---------+--------+
                                  |
                                  v
                        +------------------+
                        | Hyperledger Besu |
                        |  Private Network |
                        +---------+--------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             +-------------+            +-------------------+
             |  Chainlens  |            | Compliance Monitor|
             |  Explorer   |            | Python Rules      |
             +-------------+            +---------+---------+
                                                  |
                                                  v
                                         +------------------+
                                         | Risk / Decision  |
                                         +---------+--------+
                                                   |
                                                   v
                                         +------------------+
                                         | Compliance Case  |
                                         |      JSON        |
                                         +------------------+
```

### Fluxo principal

A transação de demonstração transfere **11 ETH** do Banco Alpha para o Custodian Gamma e foi registrada no bloco **4453** da rede local.

O Chainlens mostra a evidência on-chain, enquanto o `compliance_monitor.py` lê a mesma transação pelo JSON-RPC do Besu, resolve as entidades envolvidas, adiciona o contexto local do applicant da Sumsub e aplica regras de risco.

O resultado atual é:

```text
HIGH_VALUE_TRANSFER
Risk score: 60
Risk level: HIGH
Decision: MANUAL_REVIEW
```

### Limite da integração Sumsub

A camada de Transaction Monitoring/KYT da Sumsub não foi habilitada no sandbox utilizado. Portanto, a arquitetura atual usa Sumsub para associação de identidade e um rules engine local para decisão de risco.

---

## English

The PoC separates four responsibilities:

1. **Identity** — association between an entity and a sandbox applicant;
2. **Blockchain** — transaction execution and persistence on Hyperledger Besu;
3. **Observability** — visual inspection of the network and transactions through Chainlens;
4. **Compliance** — wallet enrichment, rule evaluation and auditable case generation.

```text
                        +------------------+
                        |      Sumsub      |
                        | Applicant / IDV  |
                        +---------+--------+
                                  |
                                  | identity / context
                                  v
+----------------+        +------------------+
|  Banco Alpha   |------->|  Known Wallet    |
+----------------+        +---------+--------+
                                  |
                                  v
                        +------------------+
                        | Hyperledger Besu |
                        |  Private Network |
                        +---------+--------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
             +-------------+            +-------------------+
             |  Chainlens  |            | Compliance Monitor|
             |  Explorer   |            | Python Rules      |
             +-------------+            +---------+---------+
                                                  |
                                                  v
                                         +------------------+
                                         | Risk / Decision  |
                                         +---------+--------+
                                                   |
                                                   v
                                         +------------------+
                                         | Compliance Case  |
                                         |      JSON        |
                                         +------------------+
```

The main demo transaction transfers **11 ETH** from Banco Alpha to Custodian Gamma and was recorded in block **4453** on the local network.

Chainlens provides the on-chain evidence, while `compliance_monitor.py` reads the same transaction through Besu JSON-RPC, resolves the entities, adds local Sumsub applicant context and applies risk rules.

Current result:

```text
HIGH_VALUE_TRANSFER
Risk score: 60
Risk level: HIGH
Decision: MANUAL_REVIEW
```

The Sumsub Transaction Monitoring/KYT feature was not enabled in the sandbox used for this project, so the current architecture uses Sumsub for identity association and the local rules engine for transaction-risk decisions.
