# PoC 3 — Sumsub Transaction Monitoring + Hyperledger Besu

> **Projeto independente da PoC 1 e PoC 2.** Os arquivos deste projeto estão inteiramente em `poc3-sumsub-transaction-monitoring/` na branch `poc3-sumsub-transaction-monitoring`. Não execute nem edite os scripts da raiz ou da `poc2-kyb-transaction-monitoring/` para esta etapa.

## Objetivo

Conectar transações **reais de uma rede local privada Hyperledger Besu (chainId 1337)** à API **Sumsub Transaction Monitoring Sandbox**, consultar os resultados efetivamente gerados pelo provedor e guardar evidências locais auditáveis.

- A **PoC 1** continua na raiz de `compliance-monitor` (monitoramento e regras locais).
- A **PoC 2** continua na pasta `poc2-kyb-transaction-monitoring/` da branch `kyb-transaction-monitoring`.
- A **PoC 3** fica nesta pasta e nesta branch, sem alterar as anteriores.

O ambiente Besu já existente é usado **somente para leitura via JSON-RPC**: a PoC 3 **não reconfigura nem reinicia os contêineres** da PoC 1. Para demonstrar a transação histórica de 11 ETH, a mesma rede precisa estar disponível em `http://localhost:8545`.

## Arquitetura

```text
Hyperledger Besu (RPC read-only)
  └─ transação confirmada 11 ETH: Banco Alpha → Custodian Gamma
       └─ send_to_sumsub.py
            └─ Sumsub Transaction Monitoring API [SANDBOX, applicant existente]
                 └─ check_sumsub_tm.py: score/status/regras retornados
                      └─ cases/CASE-CF85CF6D.json
                         ├─ riskAssessment: motor de regras local da PoC 3 (demonstrativo)
                         └─ sumsubTransactionMonitoring: resposta da Sumsub (real)
```

## Resultado da validação — 3 de novembro de 2026

**Integração ponta a ponta comprovada no Sumsub Sandbox.**

Uma transferência histórica real da rede **Besu privada** foi lida via RPC,
convertida para o payload de negócio e enviada ao **Transaction Monitoring**
da Sumsub com o applicant de teste já existente.

| Evidência | Valor confirmado |
|---|---|
| Transferência | Banco Alpha → Custodian Gamma, 11 ETH |
| Blockchain | Besu privada, chainId 1337, bloco 4453 |
| Sumsub API — consulta por txnId | HTTP 200 |
| Sumsub TM score | 60 |
| Sumsub TM reviewStatus | `onHold` |
| Regras que corresponderam | 1 |
| Nome da regra | `POC3 - Transferencia de alto valor de ETH` |
| Status no Dashboard | Requer uma ação |
| Etiqueta | Valor muito alto |
| Evidência JSON local | `cases/CASE-CF85CF6D.json` |

A **decisão de revisão manual ainda não foi tomada** (`reviewAnswer: N/A`);
o estado atual é **em espera para análise**, não uma rejeição da transação.
A evidência foi validada pelo retorno da API e visualmente no painel Sandbox.
O case completo continua armazenado **localmente**, ignorado pelo Git.

O score de 60 no **motor local** e o score de 60 na **Sumsub** são avaliações
independentes, que por acaso coincidiram devido às regras deste cenário.
O fluxo não equivale a análise independente do histórico on-chain de uma
blockchain privada pela Sumsub, e não implementa Travel Rule.

**Segurança do case:** a partir da atualização de 3 de novembro de 2026,
executar novamente `compliance_monitor.py` atualiza somente os campos locais e
**preserva** `sumsubTransactionMonitoring` já registrado.

## Arquivos principais

- `send_to_sumsub.py` — lê hash e bloco do Besu e envia a transação de negócio para o TM Sandbox após confirmação.
- `check_sumsub_tm.py` — consulta a transação Sumsub por `txnId`.
- `sumsub_tm_case.py` — persiste o resultado do TM sem confundi-lo com o score local.
- `compliance_monitor.py` — gera o relatório local independente (não é score Sumsub).
- `sumsub_client.py` — assina a API com credenciais lidas **somente do .env desta pasta**.
- `test_sumsub_tm.py` — testa API de moedas disponíveis (não envia transações).
- `test_sumsub_tm_integration.py` — testes locais sem credenciais nem rede;
- `review_sumsub_tm.py` — consulta a revisão; conclusão por API somente sob confirmação explícita;
- `demo_case_report.py` — relatório HTML local para gravação do vídeo;
- `VIDEO_DEMO.md` — roteiro preliminar com cenas Sumsub, Besu e trilha de auditoria.
- `entities.json` e `sumsub_applicants.json` — associação local entre carteira, entidade fictícia e applicant Sandbox.

## Instalação em NOVA pasta no Ubuntu/WSL

Faça um clone **separado**, fora do diretório já utilizado pelas PoCs 1 e 2:

```bash
cd ~
git clone --single-branch --branch poc3-sumsub-transaction-monitoring \
  https://github.com/mcreimer/poc-compliance-digital-assets.git \
  poc3-sumsub-tm

cd ~/poc3-sumsub-tm/poc3-sumsub-transaction-monitoring
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cp .env.example .env
cp sumsub_applicants.example.json sumsub_applicants.json
```

Edite apenas os arquivos `.env` e `sumsub_applicants.json` **dentro desta pasta**. Insira suas credenciais do Sandbox e o `applicantId` já cadastrado para `BANK_ALPHA`. Nunca publique token, secret key nem o arquivo real de applicants.

## Teste em etapas

Na pasta `~/poc3-sumsub-tm/poc3-sumsub-transaction-monitoring`:

```bash
python -m unittest test_sumsub_tm_integration.py
python test_rpc.py
python test_sumsub_env.py
python test_sumsub_tm.py
```

Transação original de 11 ETH (`block 4453`):

```text
0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

Gere o case local somente nesta pasta:

```bash
python compliance_monitor.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

Simule o envio (sem chamadas API):

```bash
python send_to_sumsub.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c \
  --dry-run
```

Somente quando a configuração estiver validada, envie após a confirmação interativa:

```bash
python send_to_sumsub.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

Consulte o TM após processar:

```bash
python check_sumsub_tm.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

O resultado real fica em `cases/CASE-CF85CF6D.json` (arquivo local ignorado pelo Git). No Dashboard da Sumsub (modo Sandbox), procure em **Monitoring → Transactions and activity**. Para o GET, o token precisa da permissão **View TM transactions**.

## Investigação e tratamento do alerta (etapa adicional)

**Status verificado em 03/11/2026:** consulta TM `HTTP 200`,
`score: 60`, `reviewStatus: onHold`, `reviewAnswer: N/A`,
uma regra acionada: `POC3 - Transferencia de alto valor de ETH`.
O ID interno retornado pela Sumsub foi `6aea325be4c626267f805024`.
A decisão de compliance **não foi concluída**.

Esta evolução foi preparada para um **vídeo demonstrativo**. Antes de
aprovar ou rejeitar, gravar o alerta em estado `onHold` no Dashboard.

**1. Inspeção segura (somente GET)**

```bash
python review_sumsub_tm.py \
  --tx-hash 0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c
```

O comando consulta a resposta atual e atualiza o registro local sem
alterar a decisão da Sumsub.

**2. Atribuição e notas no Dashboard**

- Abra **Monitoramento de transações → Transações**.
- Atribua a transação em **Pessoa designada** ou no detalhe da transação.
- Abra a transação, examine pontuação/regras e adicione uma nota na seção **Notas**.
- Para essa operação, sua conta precisa da permissão
  **Manage TM transactions - Review**.

**3. Gerar relatório visual para o vídeo**

```bash
python demo_case_report.py --case cases/CASE-CF85CF6D.json
```

Abra `cases/DEMO-CASE-CF85CF6D.html` em um navegador. O HTML resume os
atributos relevantes e a linha do tempo das respostas observadas, sem
publicar o payload integral da Sumsub.

**4. Decisão manual (opcional e somente quando tiver gravado o onHold)**

A decisão pode ser tomada pelo próprio Dashboard Sumsub. Depois, execute
novamente o comando `review_sumsub_tm.py` para registrar a transição
`onHold → completed` e `GREEN` ou `RED` no case local.

Também está disponível uma alternativa por API, deliberadamente bloqueada
até a confirmação explícita de `--decision`, do ID interno da transação
e de uma frase digitada no terminal:

```bash
# Exemplo: somente se decidir APROVAR explicitamente no Sandbox.
# Não executar durante preparação do vídeo.
# python review_sumsub_tm.py --tx-hash <HASH> --decision approve --confirm-sumsub-id <SUMSUB_INTERNAL_ID>
```

Para essas decisões, o token necessita da permissão
**Manage TM transactions - Decisions**. A decisão não é reversível pelo
script: use apenas um Sandbox e confira o caso antes de agir.

**Roteiro detalhado com sequência de telas e falas:** [VIDEO_DEMO.md](VIDEO_DEMO.md).
A regra que já está funcionando será **mostrada no Dashboard**; não
precisaremos recriá-la durante o vídeo.

## Regra de teste e limitações

Neste cenário foi configurada e ativada no Sandbox a regra `POC3 - Transferencia de alto valor de ETH`, que corresponde a **11 ETH na chain 1337**, adiciona **60 pontos**, aplica a etiqueta **Valor muito alto** e coloca a transação **em espera para revisão**. Outras transações ou regras podem gerar resultados diferentes.

A Sumsub recebe atributos informados pelo sistema de origem, mas **não consegue comprovar automaticamente o hash da Besu privada em exploradores ou serviços de análise de blockchains públicas**. Crypto screening e alertas baseados em exposição on-chain pública podem não funcionar para a chain 1337. A PoC demonstra Transaction Monitoring, **não validação de Travel Rule** nem controles AML de produção.

Os dados de `entities.json` e os thresholds do motor local são **fictícios/demonstrativos**. Resultados API são mostrados separadamente dos resultados locais. O app token deve ser `sbx:`; o script bloqueia envio com token de produção.

### Documentação oficial da API
- [Enviar transação para applicant existente](https://docs.sumsub.com/reference/submit-transaction-for-existing-applicant)
- [Consultar transação por txnId](https://docs.sumsub.com/reference/get-transaction-information-by-txnid)
- [Guia de início rápido Transaction Monitoring](https://docs.sumsub.com/docs/transaction-monitoring-quick-start-guide)
