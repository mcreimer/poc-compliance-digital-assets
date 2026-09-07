# Simple Crypto Compliance PoC

Uma PoC mínima para demonstrar:

- KYB de instituições
- Transaction Monitoring / KYT
- Análise de risco de transações
- Alertas de compliance
- Uma visão simples para investigação

## Objetivo

Esta primeira versão **não usa blockchain real**.

Ela simula transações entre instituições que poderiam estar em uma rede permissionada (por exemplo, Hyperledger Besu).
A ideia é validar primeiro a lógica de compliance. Depois podemos conectar a mesma lógica a Besu, FireFly ou a uma ferramenta de blockchain analytics.

## Requisitos

- Python 3.9 ou superior
- Nenhuma biblioteca externa

## Como executar

No terminal:

```bash
python poc.py
```

O programa:

1. carrega as empresas e seus status de KYB;
2. carrega as transações;
3. aplica regras simples de risco;
4. mostra os resultados no terminal;
5. gera o arquivo `report.html`.

Abra `report.html` no navegador para ver o painel.

## Regras desta versão

- KYB não aprovado: +70
- Entidade de alto risco: +30
- Transação acima de R$ 100.000: +25
- Destino marcado como wallet de alto risco: +50
- Destino com sanctions match: +100
- Rapid pass-through: +35

Classificação:

- 0–29: CLEAR
- 30–59: REVIEW
- 60–99: ALERT
- 100+: CRITICAL

## Cenário

As empresas são fictícias:

- Banco Alpha
- Exchange Beta
- Fintech Delta
- Custodian Gamma

Exemplos incluídos:

- transferência normal;
- transação de alto valor;
- rapid pass-through;
- transferência para endereço de alto risco;
- contraparte sem KYB aprovado.

## Próximas fases

### Fase 2
Substituir as transações simuladas por transações reais em uma rede Hyperledger Besu local.

### Fase 3
Capturar eventos do smart contract automaticamente.

### Fase 4
Adicionar FireFly.

### Fase 5
Trocar o `mock blockchain intelligence` por integração com Elliptic, Chainalysis, TRM ou outro provider.

A vantagem desta abordagem é que a lógica de compliance permanece praticamente a mesma.
