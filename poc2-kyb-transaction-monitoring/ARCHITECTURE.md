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


## Motor de monitoramento transacional

O motor mantém contexto sobre uma sequência de eventos e aplica regras sobre janelas temporais.

```text
Entradas abaixo do limite
        |
        +--> soma em 30 minutos >= 10 ETH
        |        |
        |        v
        |    ESTRUTURACAO (+30)
        |
        v
Saída da Fintech Delta
        |
        +--> >= 75% do valor recebido em até 15 minutos
        |        |
        |        v
        |    PASSAGEM_RAPIDA_DE_FUNDOS (+25)
        |
        +--> destino = contraparte HIGH/CRITICAL
                 |
                 v
             CONTRAPARTE_ALTO_RISCO (+30)
```

O contexto de KYB é incorporado separadamente:

```text
Risco corporativo KYB: 35
Risco transacional:    85
                         +
                      -----
Score combinado:       100 (limitado a 100)
```

O sinal `UBO_ALTO_RISCO` é exibido no caso como contexto, mas não soma pontos novamente, pois o risco do UBO já participa do score corporativo.

## Saída para investigação

A decisão `ESCALAR_CASO` gera um registro consolidado contendo:

- perfil KYB e UBOs;
- achados corporativos;
- sequência de transações analisadas;
- parâmetros das janelas temporais;
- evidência de cada regra;
- score transacional;
- score combinado;
- decisão final.

Na próxima etapa, os eventos demonstrativos serão substituídos por transações reais recuperadas do Hyperledger Besu.
