#!/usr/bin/env python3
"""Create a video-friendly, read-only HTML summary of a local PoC 3 case.

Usage: python demo_case_report.py --case cases/CASE-CF85CF6D.json
Generated HTML stays under cases/ (ignored by Git) and shows only selected
fictional case details; it does not include the full Sumsub response or tokens.
"""
import argparse
import html
import json
from pathlib import Path


def esc(value):
    if value is None:
        return "Não informado"
    return html.escape(str(value), quote=True)


def main():
    parser = argparse.ArgumentParser(description="Gerar relatório visual local da PoC 3.")
    parser.add_argument("--case", required=True, type=Path, help="Arquivo CASE-*.json.")
    args = parser.parse_args()
    if not args.case.exists():
        parser.error("Case local não encontrado; execute check_sumsub_tm.py primeiro.")

    case = json.loads(args.case.read_text(encoding="utf-8"))
    txn = case.get("transaction") or {}
    tm = case.get("sumsubTransactionMonitoring") or {}
    local = case.get("riskAssessment") or {}
    sender = (case.get("sender") or {}).get("name", "Banco Alpha (PoC)")
    counterparty = (case.get("counterparty") or {}).get(
        "name", "Custodian Gamma (PoC)"
    )
    rules = tm.get("matchedRules") or []
    rule_html = "".join(
        "<li>" + esc(r.get("title") or r.get("name") or r.get("id")) + "</li>"
        for r in rules
    ) or "<li>Nenhuma regra retornada</li>"

    timeline = case.get("sumsubMonitoringTimeline") or []
    if not timeline and tm.get("reviewStatus"):
        timeline = [{
            "reviewStatus": tm.get("reviewStatus"),
            "reviewAnswer": tm.get("reviewAnswer"),
            "score": tm.get("score"),
            "observedAt": tm.get("lastUpdatedAt"),
        }]
    timeline_html = "".join(
        "<div class='event'><b>" + esc(item.get("reviewStatus")) +
        "</b> <small>" + esc(item.get("observedAt") or "") +
        "</small><div>Score: " + esc(item.get("score")) +
        " · Decisão: " + esc(item.get("reviewAnswer") or "Pendente") +
        "</div></div>"
        for item in timeline
    ) or "<p>Sem alterações registradas</p>"

    is_on_hold = tm.get("reviewStatus") == "onHold"
    status_caption = "AGUARDANDO ANÁLISE" if is_on_hold else (
        "REVISÃO CONCLUÍDA" if tm.get("reviewStatus") == "completed"
        else "STATUS EM CONSULTA"
    )
    answer = tm.get("reviewAnswer") or "Pendente"
    provider_id = tm.get("sumsubTxnId") or "N/A"
    txn_id = tm.get("txnId") or "N/A"

    content = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PoC 3 | Evidências Sumsub Transaction Monitoring</title>
<style>
:root{color-scheme:light;--ink:#17263f;--muted:#607089;--line:#dfe7ef;--blue:#175bdd;--bg:#f3f6fa}
*{box-sizing:border-box}
body{margin:0;font:16px/1.5 system-ui,-apple-system,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink)}
main{max-width:1220px;margin:24px auto;padding:0 20px}
header{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:22px}
h1{font-size:31px;letter-spacing:-.6px;margin:2px 0}
.subtitle,.muted{color:var(--muted)}
.brand{font-weight:750;color:var(--blue);letter-spacing:.8px}
.pill{font-size:12px;padding:7px 12px;border-radius:99px;background:#e6eefc;color:#174ac5;font-weight:750}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{border:1px solid var(--line);background:white;border-radius:15px;padding:23px;box-shadow:0 5px 18px #1d2c4007}
.wide{grid-column:1/-1}
.kpi{display:flex;justify-content:space-between;gap:16px}
.kpi strong{font-size:39px;letter-spacing:-1.2px}
.label{font-size:12px;text-transform:uppercase;letter-spacing:1px;font-weight:700;color:var(--muted)}
.status{font-size:13px;letter-spacing:1px;font-weight:800;color:#9e6200}
h2{font-size:19px;margin:0 0 15px}
table{width:100%;border-collapse:collapse}
td{padding:11px 0;border-bottom:1px solid var(--line);vertical-align:top}
td:first-child{color:var(--muted);width:34%}
code{font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}
.flow{display:flex;gap:10px;align-items:center;justify-content:space-between;flex-wrap:wrap}
.flow span{padding:12px 14px;border-radius:8px;background:#edf3ff;font-weight:700;color:#175bdd}
.flow .arrow{background:none;color:#7c8ca6}
ul{padding-left:22px}
.event{padding:13px 0;border-bottom:1px solid var(--line)}
.event small{display:block;color:var(--muted)}
footer{margin:25px 0;color:var(--muted);font-size:12px}
@media(max-width:760px){.grid{grid-template-columns:1fr}.wide{grid-column:auto}h1{font-size:24px}header{align-items:flex-start;flex-direction:column}.flow .arrow{display:none}}
</style></head>
<body><main>
<header><div><div class="brand">MCTrade · Digital Asset Compliance</div>
<h1>PoC 3 — Transaction Monitoring</h1>
<div class="subtitle">Hyperledger Besu + Sumsub · Demonstração técnica</div></div>
<div class="pill">SANDBOX • DADOS FICTÍCIOS</div></header>
<div class="card wide" style="margin-bottom:16px"><div class="flow">
<span>Besu · bloco __BLOCK__</span><span class="arrow">→</span>
<span>Integração Python</span><span class="arrow">→</span>
<span>Sumsub TM</span><span class="arrow">→</span>
<span>Revisão manual</span></div></div>
<div class="grid">
<section class="card"><div class="label">Transferência registrada no Besu</div>
<div class="kpi"><strong>__AMOUNT__ ETH</strong><div class="pill">Chain ID 1337</div></div>
<p><b>__SENDER__</b> → <b>__RECIPIENT__</b></p>
<table><tr><td>Bloco</td><td>__BLOCK__</td></tr>
<tr><td>Hash</td><td><code>__HASH__</code></td></tr>
<tr><td>Confirmação da transação</td><td>__TXSTATUS__</td></tr></table></section>
<section class="card"><div class="label">Resultado Sumsub Transaction Monitoring</div>
<div class="kpi"><strong>__SCORE__</strong><span class="status">__STATE__</span></div>
<table><tr><td>reviewStatus</td><td><b>__REVIEWSTATUS__</b></td></tr>
<tr><td>reviewAnswer</td><td>__REVIEWANSWER__</td></tr>
<tr><td>Regras acionadas</td><td>__RULECOUNT__</td></tr>
<tr><td>Identificador TM</td><td><code>__SUMSUBID__</code></td></tr></table></section>
<section class="card"><h2>Regras de monitoramento acionadas</h2>
<ul>__RULES__</ul>
<p class="muted">A avaliação é calculada pela plataforma Sumsub Sandbox. Não equivale a blockchain analytics independente para uma rede privada.</p></section>
<section class="card"><h2>Avaliação demonstrativa local</h2>
<table><tr><td>Score local</td><td>__LOCALSCORE__</td></tr>
<tr><td>Decisão local</td><td>__LOCALDECISION__</td></tr>
<tr><td>Case ID</td><td><code>__CASEID__</code></td></tr>
<tr><td>Txn ID externo</td><td><code>__EXTERNALID__</code></td></tr></table>
<p class="muted">O score local é independente do score da Sumsub, mesmo que os valores coincidam.</p></section>
<section class="card wide"><h2>Evolução do alerta registrada localmente</h2>
__TIMELINE__</section></div>
<footer>Prova de conceito educacional · Não é sistema AML/KYT de produção · Dados fictícios e resposta real da API Sandbox.</footer>
</main></body></html>"""
    subst = {
        "__AMOUNT__": txn.get("amount", "11"),
        "__BLOCK__": txn.get("block", "4453"),
        "__SENDER__": sender,
        "__RECIPIENT__": counterparty,
        "__HASH__": txn.get("hash", ""),
        "__TXSTATUS__": txn.get("status", "Confirmada"),
        "__SCORE__": tm.get("score"),
        "__STATE__": status_caption,
        "__REVIEWSTATUS__": tm.get("reviewStatus"),
        "__REVIEWANSWER__": answer,
        "__RULECOUNT__": len(rules),
        "__RULES__": rule_html,
        "__SUMSUBID__": provider_id,
        "__LOCALSCORE__": local.get("score"),
        "__LOCALDECISION__": local.get("decision"),
        "__CASEID__": case.get("caseId"),
        "__EXTERNALID__": txn_id,
        "__TIMELINE__": timeline_html,
    }
    for key, value in subst.items():
        content = content.replace(
            key, value if key in {"__RULES__", "__TIMELINE__"} else esc(value)
        )
    out = args.case.parent / ("DEMO-" + args.case.stem + ".html")
    out.write_text(content, encoding="utf-8")
    print("Relatório HTML gerado:", out)
    print("Abra no navegador como arquivo local; nenhum servidor é necessário.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
