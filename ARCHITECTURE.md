# Arquitetura da Fase 1

```text
entities.json
   |
   v
 KYB data
   |
   +----------------------+
                          |
transactions.json         |
   |                      |
   v                      v
Simulated transactions -> Compliance Engine
                              |
                              +--> KYB checks
                              +--> high-value rule
                              +--> rapid pass-through
                              +--> mock wallet risk
                              +--> sanctions match
                              |
                              v
                         Risk score
                              |
                       +------+------+
                       |             |
                    Terminal      report.html
```

## O que isto demonstra

Mesmo sem blockchain real, já conseguimos explicar em uma entrevista ou demo:

1. como uma instituição é identificada via KYB;
2. como uma transação é avaliada;
3. como sinais on-chain podem entrar no risk score;
4. como regras comportamentais podem gerar alerta;
5. como um investigador recebe a justificativa do alerta.

Na Fase 2, `transactions.json` deixa de ser a origem dos dados.
Os eventos passam a vir de um smart contract em Hyperledger Besu.
