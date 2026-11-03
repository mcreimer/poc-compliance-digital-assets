# Roteiro preliminar do vídeo — PoC 3

## Objetivo

Demonstrar, com **dados fictícios e API real em Sandbox**, o fluxo de
monitoramento transacional aplicado a uma blockchain privada:

**Hyperledger Besu → Python → Sumsub TM → regra de risco → analista → decisão → evidência.**

Vídeo educativo, 6–8 minutos (ajustável depois). Priorizar telas reais e
comportamento verificável em vez de slides longos. Mostrar Chainlens e
Prometheus/Grafana somente se estiverem funcionando; o monitoramento na Sumsub
não depende deles.

**NÃO aprovar/rejeitar a transação atual antes de gravar as telas de onHold.**
A decisão encerra o alerta. Se preferir, mantenha esta transação histórica
como evidência de onHold e prepare uma segunda transação exclusivamente para
demonstrar a decisão final.

## Ordem de gravação e falas sugeridas

| Tempo | Tela | Narração sugerida |
|---|---|---|
| 0:00–0:30 | Abertura: objetivo e arquitetura | "Nesta demonstração, conectei uma transação real de uma rede privada Hyperledger Besu ao motor de monitoramento transacional da Sumsub, em Sandbox." |
| 0:30–1:50 | **Sumsub > Monitoramento de transações > Gerenciador de regras > Regras instaladas**; abrir a regra de 10 ETH | "A regra está configurada em SumScript, considera moeda ETH e identifica nossa rede Besu privada pelo chain ID 1337. Em caso de correspondência, ela soma 60 pontos e direciona a operação para revisão manual." |
| 1:50–2:55 | Terminal RPC/Chainlens: hash, bloco 4453, 11 ETH | "A transação está registrada e confirmada no Besu. São dados on-chain de uma rede privada, não uma transferência da Ethereum pública." |
| 2:55–3:50 | Terminal: script `send_to_sumsub.py --dry-run`; mostrar resumo do JSON | "O integrador lê a transação no nó RPC, relaciona carteiras a entidades de demonstração e prepara o payload do Transaction Monitoring." |
| 3:50–4:50 | Sumsub > Transações: badge 'Requer uma ação', score 60, etiqueta 'Valor muito alto'; detalhes de regras acionadas | "A plataforma recebeu a transação por API e executou a regra. A pontuação de 60 foi retornada pela Sumsub, não calculada apenas pelo nosso monitor local." |
| 4:50–5:45 | Atribuir analista no dashboard e abrir notas | "O alerta é entregue à fila de revisão. Um analista registra a avaliação e decide como proceder; score alto é um sinal para investigar, não uma prova de ilícito." |
| 5:45–6:45 | **Somente após gravar onHold:** demonstração opcional de Aprovar/Rejeitar e nova consulta `review_sumsub_tm.py` | "Ao concluir a análise, a decisão é registrada na plataforma e o status pode ser recuperado por API." |
| 6:45–7:30 | Relatório HTML local `DEMO-CASE-CF85CF6D.html` e conclusão | "Preservamos o histórico da avaliação para auditoria, separando as regras locais dos resultados efetivamente produzidos pela Sumsub." |

### Captura da regra no Dashboard — prioridade do vídeo

1. Confirmar **Sandbox** pela faixa amarela.
2. Abrir **Monitoramento de transações → Gerenciador de regras → Regras instaladas**.
3. Abrir **POC3 - Transferencia de alto valor de ETH**.
4. Mostrar condição:

```text
data.info.amount >= 10 AND
data.info.currencyCode = 'ETH' AND
data.props.chainId = '1337'
```

5. Mostrar **Colocar em espera**, **Pontuação: +60** e etiqueta
   **Valor muito alto**.
6. Mostrar que a regra está ativa. **Não é necessário recriá-la durante
   o vídeo**; já temos evidência de que foi executada. Recriar pode
   introduzir duplicação e alterar a demonstração.

### Anotação sugerida para o analista (apenas Sandbox)

"PoC 3 — Análise demonstrativa: transferência de 11 ETH entre Banco Alpha e
Custodian Gamma, registrada no bloco 4453 da rede Besu privada (chainId 1337).
Regra de valor elevado acionada, score Sumsub 60 e status onHold. As entidades
e classificações KYB são fictícias. Em ambiente real, seria necessária revisão
de identidade, origem/destino dos ativos, histórico transacional e exposição
a riscos antes da decisão final."

Pode adicionar esta nota em **Sumsub > Monitoramento de transações >
Transações > [abrir transação] > Notas > Adicionar nota**.
Atribua o analista pela coluna **Pessoa designada**. Essas ações podem
depender da permissão **Manage TM transactions - Review**.

### Executar comandos para a demonstração

Dentro da pasta exclusiva da PoC 3:

```bash
python review_sumsub_tm.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c

python demo_case_report.py --case cases/CASE-CF85CF6D.json
```

Abra o relatório local `cases/DEMO-CASE-CF85CF6D.html` no navegador.
É um resumo visual do JSON, **não um PDF oficial** da Sumsub.

### Decisão final (OPCIONAL, somente depois da gravação do onHold)

Há duas maneiras:

1. **Preferível para o vídeo:** Sumsub > Monitoramento de transações >
   Transações > [transação] > Aprovar ou Rejeitar. Registrar a
   decisão pela interface. A Sumsub confirma a decisão manualmente tomada.
2. **Alternativa técnica:** usar `review_sumsub_tm.py` com `--decision`
   e `--confirm-sumsub-id`, mais uma confirmação textual. Requer
   token Sandbox com `Manage TM transactions - Decisions`.

```bash
# Primeiro inspecionar e confirmar ID/status, SEM modificar:
python review_sumsub_tm.py --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c

# EXEMPLO SOMENTE PARA QUANDO VOCÊ DECIDIR APROVAR NO SANDBOX:
# python review_sumsub_tm.py --tx-hash <HASH> --decision approve --confirm-sumsub-id <ID_INTERNO_DA_SUMSUB>
```

Se tomar a decisão no Dashboard, execute o primeiro comando novamente depois
para registrar `completed` e `GREEN`/`RED` no histórico local.

### Segurança e precisão editorial

- Ocultar segredos de `.env`, tokens, senhas, e-mails reais e informações
  de conta antes de gravar telas.
- Todas as identidades corporativas do exemplo são fictícias.
- Não apresentar a PoC como sistema AML em produção.
- **Não afirmar que a Sumsub fez análise independente de blockchain
  analytics sobre o hash da Besu privada**. Demonstramos monitoramento
  dos atributos de negócio enviados pela API e a execução de regras.
- Diferenciar `riskAssessment` (score local) de
  `sumsubTransactionMonitoring` (score e reviewStatus reais).
- A PoC não demonstra, por si só, interoperabilidade da Travel Rule.
- Deixar parte técnica de contêineres, RPC, Chainlens/Grafana em cerca de
  1–2 minutos; o centro do vídeo é o fluxo Sumsub de ponta a ponta.

### Capturas que precisamos preservar

Antes de encerrar o alerta:
- Página da regra com SumScript e ação;
- Transação Besu e hash/bloco;
- Sumsub com badge 'Requer uma ação' e score 60;
- Detalhe de regras acionadas;
- Atribuição do analista e a nota.

Depois de tomar a decisão:
- Status final e eventos de alteração no Dashboard;
- Resultado atualizado do CLI de consulta;
- Relatório HTML com linha do tempo.
