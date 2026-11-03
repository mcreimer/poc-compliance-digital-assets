#!/usr/bin/env python3
"""Video-ready, offline HTML presentation of verified PoC 3 compliance cases.

No network calls, external fonts/assets, secrets or raw Sumsub responses.
Single-case mode remains compatible with the original invocation.
"""
import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from string import Template


def esc(value, fallback="Não informado"):
    """Escape any value before placing it in an HTML context."""
    if value is None or value == "":
        return html.escape(fallback, quote=True)
    return html.escape(str(value), quote=True)


def status_info(tm):
    review = str(tm.get("reviewStatus") or "")
    answer = str(tm.get("reviewAnswer") or "")
    if review == "completed" and answer == "GREEN":
        return ("Aprovada manualmente", "approved", "Concluída", "GREEN")
    if review == "completed" and answer == "RED":
        return ("Rejeitada manualmente", "rejected", "Concluída", "RED")
    if review == "completed":
        return ("Revisão concluída", "neutral", "Concluída", answer or "Não informado")
    if review == "onHold":
        return ("Aguardando revisão", "holding", "Em espera", "Pendente")
    return ("Estado não confirmado", "neutral", review or "Sem status", answer or "Pendente")


def pretty_score(score):
    if score is None:
        return "—", 0
    try:
        number = float(score)
        bounded = max(0, min(100, number))
        return f"{number:g}", bounded
    except (ValueError, TypeError):
        return str(score), 0


def date_label(timestamp):
    if not timestamp:
        return "Horário não registrado"
    try:
        dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            # All original observations retain their own timestamps;
            # local conversion here is only for screen presentation.
            from zoneinfo import ZoneInfo
            dt = dt.astimezone(ZoneInfo("America/Sao_Paulo"))
            return dt.strftime("%d/%m/%Y · %H:%M BRT")
        return dt.strftime("%d/%m/%Y · %H:%M")
    except (ValueError, ImportError, KeyError):
        return str(timestamp)


def render_timeline(case, tm):
    snapshots = case.get("sumsubMonitoringTimeline") or []
    if not snapshots and tm.get("reviewStatus"):
        snapshots = [{
            "reviewStatus": tm.get("reviewStatus"),
            "reviewAnswer": tm.get("reviewAnswer"),
            "observedAt": tm.get("lastUpdatedAt"),
            "score": tm.get("score"),
        }]
    if not snapshots:
        return '<p class="empty">Nenhum estado histórico registrado no case.</p>'

    pieces = []
    for pos, item in enumerate(snapshots):
        title, klass, _, answer = status_info(item)
        is_last = pos == len(snapshots) - 1
        pieces.append(
            f'<div class="timeline-item {klass}">'
            '<div class="timeline-point" aria-hidden="true"></div>'
            '<div class="timeline-content">'
            f'<div class="timeline-head"><strong>{esc(title)}</strong>'
            f'<span>{esc(date_label(item.get("observedAt")))}</span></div>'
            '<div class="timeline-detail">'
            f'Status API: <code>{esc(item.get("reviewStatus"))}</code>'
            f'<span class="dot-sep">·</span> Score: {esc(item.get("score"))}'
            f'<span class="dot-sep">·</span> Decisão: {esc(answer)}'
            + ('<span class="latest">Última observação</span>' if is_last else '')
            + '</div></div></div>'
        )
    return "".join(pieces)


def render_case(case, idx=0):
    txn = case.get("transaction") or {}
    network = case.get("network") or {}
    tm = case.get("sumsubTransactionMonitoring") or {}
    local = case.get("riskAssessment") or {}
    rules = tm.get("matchedRules") or []
    case_id = case.get("caseId") or f"CASE-{idx + 1:02}"
    status, klass, phase, decision = status_info(tm)
    score_display, score_width = pretty_score(tm.get("score"))
    amount = txn.get("amount")
    amount_label = f'{amount:g}' if isinstance(amount, (int, float)) else esc(amount, "—")
    sender = (case.get("sender") or {}).get("name") or "Origem não identificada"
    destination = (case.get("counterparty") or {}).get("name") or "Destino não identificado"
    chain = network.get("chainId")
    block = txn.get("block")
    hash_ = txn.get("hash")
    receipt = txn.get("status")
    confirmed = "Confirmada" if receipt in (1, "1", "0x1") else "Status não verificado"
    if receipt in (0, "0", "0x0"):
        confirmed = "Falhou no Besu"
    elif receipt is None:
        confirmed = "Comprovante não disponível no case"

    rule_blocks = []
    for rule in rules:
        name = rule.get("title") or rule.get("name") or rule.get("id")
        rule_blocks.append(
            f'<div class="rule-row"><span class="small-mark">✓</span>'
            f'<div><strong>{esc(name)}</strong>'
            '<span class="detail">Correspondência confirmada pela API da Sumsub</span>'
            '</div></div>'
        )
    if not rule_blocks:
        rule_blocks.append(
            '<p class="empty">Nenhuma regra correspondente informada pela API.</p>'
        )

    local_score = local.get("score")
    local_decision = local.get("decision")
    local_available = local_score is not None or local_decision is not None

    rule_html = "".join(rule_blocks)
    history_html = render_timeline(case, tm)
    status_text = esc(status)
    score_txt = esc(score_display)
    # Do not show fictitious local decision if case lacks a local assessment.
    if local_available:
        local_html = (
            '<div class="local-kpis">'
            f'<div><small>Score local</small><b>{esc(local_score)}</b></div>'
            f'<div><small>Decisão local</small><b>{esc(local_decision)}</b></div>'
            '</div>'
        )
    else:
        local_html = '<p class="empty">Avaliação local não registrada neste case.</p>'

    return f'''
    <section class="case-panel" id="case-{idx}" data-idx="{idx}" {'hidden' if idx else ''}>
      <div class="case-heading">
        <div>
          <div class="eyebrow">Caso {idx + 1:02} <span class="subtle-sep">/</span> {esc(case_id)}</div>
          <h2>{esc(amount_label)} <span class="unit">ETH</span><span class="case-arrow">→</span>
              <span class="case-headline">Monitoramento transacional</span></h2>
          <div class="case-direction"><span>{esc(sender)}</span><i aria-hidden="true">→</i><span>{esc(destination)}</span></div>
        </div>
        <div class="case-status {klass}"><span class="status-signal" aria-hidden="true"></span>{status_text}</div>
      </div>

      <div class="journey" aria-label="Etapas da demonstração">
        <div class="journey-node"><span class="journey-number">01</span><div>Besu <small>Transação on-chain</small></div></div>
        <span class="journey-link" aria-hidden="true">→</span>
        <div class="journey-node"><span class="journey-number">02</span><div>Python <small>Integração API</small></div></div>
        <span class="journey-link" aria-hidden="true">→</span>
        <div class="journey-node"><span class="journey-number">03</span><div>Sumsub <small>Regra e score</small></div></div>
        <span class="journey-link" aria-hidden="true">→</span>
        <div class="journey-node final"><span class="journey-number">04</span><div>{esc(phase)} <small>Revisão humana</small></div></div>
      </div>

      <div class="metrics">
        <div class="metric"><div class="metric-title">Valor transferido <span>Besu</span></div>
          <div class="metric-value">{esc(amount_label)}<span> ETH</span></div>
          <div class="metric-sub">Bloco #{esc(block)}</div></div>
        <div class="metric"><div class="metric-title">Score de risco <span>Sumsub API</span></div>
          <div class="metric-value">{score_txt}<span> / 100</span></div>
          <div class="score-track"><div class="score-fill" style="width:{score_width:g}%"></div></div></div>
        <div class="metric"><div class="metric-title">Regras acionadas <span>Sumsub API</span></div>
          <div class="metric-value">{len(rules):02}</div>
          <div class="metric-sub">Regra(s) correspondente(s)</div></div>
        <div class="metric decision"><div class="metric-title">Decisão manual <span>Sumsub API</span></div>
          <div class="metric-value compact">{esc(decision)}</div>
          <div class="metric-sub">reviewStatus: {esc(tm.get("reviewStatus"))}</div></div>
      </div>

      <div class="content-grid">
        <article class="panel">
          <div class="panel-header"><div><small class="overline">EVIDÊNCIA 01</small><h3>Transação on-chain</h3></div><span class="source">Besu · RPC</span></div>
          <div class="fact-line"><span>Origem</span><b>{esc(sender)}</b></div>
          <div class="fact-line"><span>Destino</span><b>{esc(destination)}</b></div>
          <div class="fact-line"><span>Chain ID</span><b>{esc(chain)}</b></div>
          <div class="fact-line"><span>Bloco</span><b>{esc(block)}</b></div>
          <div class="fact-line"><span>Execução</span><b>{esc(confirmed)}</b></div>
          <div class="hash-label">HASH DA TRANSAÇÃO</div>
          <div class="hash-value">{esc(hash_)}</div>
        </article>

        <article class="panel accent-panel">
          <div class="panel-header"><div><small class="overline">EVIDÊNCIA 02</small><h3>Decisão e regras</h3></div><span class="source">Sumsub · Sandbox</span></div>
          <div class="rule-stack">{rule_html}</div>
          <div class="fact-line"><span>Status da revisão</span><b>{esc(tm.get("reviewStatus"))}</b></div>
          <div class="fact-line"><span>Resultado</span><b>{esc(tm.get("reviewAnswer"), "Pendente")}</b></div>
          <div class="fact-line"><span>ID interno</span><b class="monospace">{esc(tm.get("sumsubTxnId"))}</b></div>
          <p class="panel-note">A correspondência da regra é calculada a partir dos dados submetidos à API. Não representa rastreamento público da blockchain privada.</p>
        </article>

        <article class="panel timeline-panel">
          <div class="panel-header"><div><small class="overline">TRILHA DE AUDITORIA</small><h3>Evolução da revisão</h3></div><span class="source">Observações salvas</span></div>
          <div class="timeline">{history_html}</div>
          <p class="panel-note">A linha do tempo contém apenas estados efetivamente capturados e registrados no case local. Atribuição e observações do analista são demonstradas no Dashboard Sumsub.</p>
        </article>

        <article class="panel comparison-panel">
          <div class="panel-header"><div><small class="overline">CONTROLE DEMONSTRATIVO</small><h3>Motor de regras local</h3></div><span class="source secondary-source">Separado da Sumsub</span></div>
          {local_html}
          <p class="panel-note">O motor local e a Sumsub são sistemas independentes. Scores iguais não indicam que um foi calculado pelo outro.</p>
          <details class="technical"><summary>Ver identificadores técnicos</summary>
            <div class="technical-detail">
              <div>Case: <code>{esc(case_id)}</code></div>
              <div>txnId: <code>{esc(tm.get("txnId"))}</code></div>
              <div>Hash: <code>{esc(hash_)}</code></div>
            </div>
          </details>
        </article>
      </div>
    </section>
    '''


def render_document(cases):
    if not cases:
        raise ValueError("Informe ao menos um case.")
    nav = []
    panels = []
    for idx, case in enumerate(cases):
        tm = case.get("sumsubTransactionMonitoring") or {}
        info, klass, _, _ = status_info(tm)
        amount = (case.get("transaction") or {}).get("amount")
        amount_txt = f"{amount:g}" if isinstance(amount, (int, float)) else "—"
        cid = case.get("caseId") or f"Caso {idx + 1}"
        nav.append(
            f'<button type="button" class="case-tab { "active" if idx == 0 else "" }" '
            f'data-target="{idx}" aria-pressed="{str(idx == 0).lower()}">'
            f'<span class="tab-number">0{idx + 1}</span><span class="tab-name">{esc(amount_txt)} ETH'
            f'<small>{esc(cid)}</small></span>'
            f'<span class="tab-bullet {klass}" title="{esc(info)}"></span></button>'
        )
        panels.append(render_case(case, idx))
    generated = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    # Avoid any external dependencies: HTML, CSS, JS, and all content are local.
    template = Template(r'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>PoC 3 | Digital Asset Compliance · Sumsub</title>
<style>
:root{--bg:#07101f;--panel:#101c2b;--panel2:#142436;--line:#253951;--text:#eaf2fa;--muted:#96aec4;--teal:#5ce6c8;--blue:#79b5ff;--amber:#f0b868;--green:#65dfb0;--red:#ff898f;--radius:17px}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:radial-gradient(ellipse 95% 65% at 85% -15%,#183450 0%,transparent 75%),var(--bg);color:var(--text);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
body:before{content:"";position:fixed;inset:0;z-index:-1;opacity:.08;background-image:linear-gradient(#fff1 1px,transparent 1px),linear-gradient(90deg,#fff1 1px,transparent 1px);background-size:55px 55px}
.layout{max-width:1550px;margin:auto;padding:32px 38px 30px}
.masthead{display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid var(--line);padding-bottom:22px}
.brand{display:flex;align-items:center;gap:14px}.brand-mark{width:40px;height:40px;border:1px solid #4dcdb5;border-radius:11px;display:grid;place-items:center;color:var(--teal);font-weight:850;font-size:19px;letter-spacing:-2px;background:#14362f}
.brand-name{font-weight:850;font-size:17px;letter-spacing:.045em}.brand-description{color:var(--muted);font-size:11px;letter-spacing:.13em;text-transform:uppercase}
.top-label{color:var(--teal);border:1px solid #265f61;border-radius:20px;padding:7px 12px;font-weight:750;font-size:11px;letter-spacing:.1em}
.title-strip{display:flex;justify-content:space-between;align-items:end;gap:30px;margin:34px 0 26px}
.kicker{color:var(--teal);font-weight:750;letter-spacing:.2em;font-size:12px;text-transform:uppercase}
h1{font-size:clamp(31px,3vw,45px);line-height:1.13;letter-spacing:-.045em;margin:9px 0 10px}
.subtitle{color:var(--muted);max-width:780px;margin:0}
.presentation-toggle{cursor:pointer;border:1px solid var(--line);color:var(--text);background:#14273b;border-radius:11px;padding:11px 15px;font-weight:700;white-space:nowrap}
.presentation-toggle:hover{border-color:var(--teal)}
.case-tabs{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 22px}
.case-tab{display:flex;align-items:center;gap:12px;border:1px solid var(--line);background:#0f1b2b;color:var(--text);min-width:205px;cursor:pointer;border-radius:13px;padding:11px 15px;text-align:left}
.case-tab.active{background:#193341;border-color:#42b9a8;box-shadow:0 0 0 1px #42b9a820}
.tab-number{display:grid;place-items:center;border:1px solid #376479;color:var(--teal);font-weight:800;width:31px;height:31px;border-radius:9px;font-size:12px}
.tab-name{font-weight:800;line-height:1.25}.tab-name small{font-size:11px;color:var(--muted);font-weight:500;display:block;margin-top:3px}
.tab-bullet{margin-left:auto;width:9px;height:9px;border-radius:50%;background:var(--muted)}
.tab-bullet.holding{background:var(--amber)}.tab-bullet.approved{background:var(--green)}.tab-bullet.rejected{background:var(--red)}
.case-panel[hidden]{display:none!important}
.case-heading{display:flex;justify-content:space-between;align-items:center;gap:16px;margin:5px 0 23px}
.eyebrow{font-size:11px;font-weight:800;color:var(--muted);text-transform:uppercase;letter-spacing:.15em}.subtle-sep{color:var(--teal);padding:0 6px}
h2{font-size:clamp(26px,3vw,38px);line-height:1.18;margin:8px 0 8px;letter-spacing:-.035em}
.unit{font-size:.6em;color:var(--teal);letter-spacing:0}
.case-arrow{font-size:.65em;margin:0 16px;color:#7194ae}.case-headline{font-size:.63em;color:#b7cee0;letter-spacing:-.02em}
.case-direction{color:#bccfe2;display:flex;gap:11px;align-items:center}.case-direction i{color:var(--teal);font-style:normal}
.case-status{border-radius:999px;border:1px solid var(--line);padding:10px 16px;font-size:12px;font-weight:800;white-space:nowrap}
.case-status.holding{border-color:#806034;color:var(--amber);background:#422d183d}
.case-status.approved{border-color:#2c886e;color:var(--green);background:#1846395c}
.case-status.rejected{border-color:#914952;color:var(--red);background:#4a25314d}
.status-signal{display:inline-block;width:8px;height:8px;border-radius:50%;background:currentColor;margin-right:8px}
.journey{display:flex;align-items:center;gap:10px;background:linear-gradient(110deg,#15283c,#111c2d);padding:15px 20px;border:1px solid #263e54;border-radius:14px;margin-bottom:18px}
.journey-node{display:flex;align-items:center;gap:10px;flex:1;font-weight:800;min-width:0}
.journey-node small{display:block;color:var(--muted);font-size:11px;font-weight:500}
.journey-number{display:grid;place-items:center;flex:none;background:#173b43;border:1px solid #336e71;color:var(--teal);border-radius:9px;width:31px;height:31px;font-size:11px}
.journey-node.final .journey-number{background:#275047}.journey-link{color:#4cbcae;font-size:22px;line-height:1}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:15px;margin-bottom:18px}
.metric{background:#132337;border:1px solid #273c53;border-radius:var(--radius);padding:20px;min-height:143px}
.metric-title{display:flex;justify-content:space-between;gap:8px;color:#b5cade;font-size:12px;font-weight:700}
.metric-title span{color:var(--teal);font-size:10px;text-transform:uppercase;white-space:nowrap}
.metric-value{font-weight:850;font-size:clamp(31px,2.8vw,43px);line-height:1.25;letter-spacing:-.055em;margin:14px 0 6px}
.metric-value span{font-size:15px;font-weight:600;letter-spacing:normal;color:var(--muted)}
.metric-value.compact{font-size:clamp(26px,2vw,34px);color:var(--green)}
.metric-sub{font-size:12px;color:var(--muted)}
.score-track{height:5px;margin-top:12px;background:#304157;border-radius:99px;overflow:hidden}
.score-fill{height:100%;background:linear-gradient(90deg,var(--teal),var(--amber));border-radius:99px}
.content-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:16px}
.panel{background:#101e2e;border:1px solid var(--line);border-radius:var(--radius);padding:23px}
.accent-panel{border-color:#2b6662;background:linear-gradient(155deg,#102c34,#101d2b 75%)}
.panel-header{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:20px}
.overline{display:block;color:var(--teal);font-weight:800;letter-spacing:.14em;font-size:10px}
h3{font-size:20px;letter-spacing:-.03em;margin:5px 0 0}
.source{font-size:10px;font-weight:750;color:var(--teal);border:1px solid #285b5f;padding:5px 8px;border-radius:7px;white-space:nowrap}
.source.secondary-source{color:#9cb9d6;border-color:#41627f}
.fact-line{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-bottom:1px solid #263950;font-size:13px}
.fact-line span{color:var(--muted)}.fact-line b{text-align:right;overflow-wrap:anywhere}
.hash-label{font-size:10px;letter-spacing:.12em;font-weight:750;color:var(--muted);margin:20px 0 6px}
.hash-value,.monospace,code{font:12px/1.6 Consolas,"SFMono-Regular",monospace;overflow-wrap:anywhere}
.hash-value{background:#0a1726;padding:12px;border:1px solid #273b52;border-radius:9px;color:#a6dbf5}
.rule-stack{padding:3px 0 12px}
.rule-row{display:flex;align-items:flex-start;gap:11px;background:#1a3a3d;border:1px solid #2c615c;padding:13px;border-radius:11px;margin-bottom:8px}
.rule-row strong{display:block}.detail{display:block;font-size:11px;color:#b3d4cf;margin-top:2px}
.small-mark{background:#26665a;color:var(--green);border-radius:99px;width:21px;height:21px;text-align:center;line-height:21px;font-weight:800}
.panel-note{font-size:11px;line-height:1.65;color:var(--muted);margin:19px 0 0}
.timeline{margin:3px 0 0 8px;padding-left:18px;border-left:1px solid #315167}
.timeline-item{position:relative;padding:0 0 21px 12px}.timeline-item:last-child{padding-bottom:6px}
.timeline-point{position:absolute;top:6px;left:-25px;background:#789bb9;border:3px solid #13283a;width:13px;height:13px;border-radius:100%}
.timeline-item.holding .timeline-point{background:var(--amber)}.timeline-item.approved .timeline-point{background:var(--green)}.timeline-item.rejected .timeline-point{background:var(--red)}
.timeline-head{display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:13px}.timeline-head span{font-size:11px;color:var(--muted)}
.timeline-detail{color:#9bb6cc;font-size:12px;margin-top:3px}
.dot-sep{color:#57718a;padding:0 5px}.latest{margin-left:8px;padding:3px 7px;border:1px solid #28675f;border-radius:6px;color:var(--teal);font-size:10px}
.local-kpis{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:11px}
.local-kpis>div{background:#152a3d;border-radius:10px;padding:16px}
.local-kpis small{display:block;color:var(--muted);font-size:11px}.local-kpis b{display:block;font-size:20px;margin-top:8px;overflow-wrap:anywhere}
.empty{color:var(--muted);font-size:13px}
.technical{border-top:1px solid #2b3e55;margin-top:18px;padding-top:12px;font-size:12px}
.technical summary{color:#a1dce2;cursor:pointer;font-weight:700}.technical-detail{margin-top:11px;color:var(--muted)}.technical-detail div{margin-bottom:6px}
footer{border-top:1px solid var(--line);margin-top:26px;padding:16px 0;color:var(--muted);font-size:11px;display:flex;justify-content:space-between;gap:20px}
footer strong{color:var(--teal)}.presentation .layout{max-width:1800px;padding:22px 32px}
.presentation .title-strip{margin:22px 0 16px}.presentation .metrics{gap:12px}
.presentation .metric{min-height:121px;padding:17px}
.presentation .panel{padding:20px}.presentation footer{display:none}
button:focus-visible,summary:focus-visible{outline:3px solid var(--teal);outline-offset:3px}
@media(max-width:1100px){.metrics{grid-template-columns:repeat(2,1fr)}.content-grid{grid-template-columns:1fr}}
@media(max-width:700px){.layout{padding:19px}.masthead{align-items:start}.title-strip,.case-heading{flex-direction:column;align-items:flex-start}.case-tabs{flex-direction:column}.case-tab{width:100%}.metrics{grid-template-columns:1fr}.journey{flex-wrap:wrap}.journey-node{flex:1 1 38%}.journey-link{display:none}footer{flex-direction:column}}
@media print{body{background:white;color:#17263b}body:before{display:none}.layout{padding:0}.case-tabs,.presentation-toggle{display:none}.case-panel[hidden]{display:block!important;break-before:page}.panel,.metric,.journey{background:#fff!important;color:#17263b!important;border-color:#bbc9d4!important;break-inside:avoid}.subtitle,.panel-note,.fact-line span,.metric-sub,.timeline-detail{color:#52667b}.fact-line,.panel{color:#17263b}.metric-title{color:#52667b}.case-heading h2{color:#17263b}footer{color:#52667b}}
</style></head><body>
<div class="layout">
<header class="masthead"><div class="brand"><div class="brand-mark" aria-hidden="true">M</div>
<div><div class="brand-name">MCTRADE <span style="color:var(--teal)">/</span> DIGITAL ASSETS</div>
<div class="brand-description">Compliance engineering · Technical demonstration</div></div></div>
<div class="top-label">● SUMSUB SANDBOX <span style="color:#779d9b">/</span> Besu 1337</div></header>
<div class="title-strip"><div><div class="kicker">Prova de conceito / 03</div>
<h1>Compliance transacional, na prática.</h1>
<p class="subtitle">Da transação on-chain à análise de risco e à decisão humana.
Evidências retornadas pela API da Sumsub, com trilha local auditável.</p></div>
<button type="button" class="presentation-toggle" id="presentation">⛶ Modo apresentação</button></div>
<nav class="case-tabs" aria-label="Selecionar cenário de demonstração">$nav</nav>
$panels
<footer><span><strong>PoC demonstrativa</strong> · Entidades fictícias · Blockchain privada · Nenhuma validação de Travel Rule ou AML de produção</span>
<span>Relatório local gerado em $generated</span></footer></div>
<script>
(() => {
  const tabs = [...document.querySelectorAll('.case-tab')];
  const panels = [...document.querySelectorAll('.case-panel')];
  let active = 0;
  function show(index) {
    if (index < 0 || index >= panels.length) return;
    active = index;
    panels.forEach((p,i) => p.hidden = i !== index);
    tabs.forEach((b,i) => {
      b.classList.toggle('active', i === index);
      b.setAttribute('aria-pressed', String(i === index));
    });
  }
  tabs.forEach((t,i) => t.addEventListener('click',() => show(i)));
  document.getElementById('presentation').addEventListener('click', () => {
    document.body.classList.toggle('presentation');
    document.getElementById('presentation').textContent =
      document.body.classList.contains('presentation') ?
        '⊞ Sair da apresentação' : '⛶ Modo apresentação';
  });
  document.addEventListener('keydown',e => {
    if (e.target.closest('input,textarea,select')) return;
    if (e.key === 'ArrowRight') show((active+1)%panels.length);
    if (e.key === 'ArrowLeft') show((active+panels.length-1)%panels.length);
  });
})();
</script></body></html>''')
    return template.substitute(nav="".join(nav), panels="".join(panels), generated=esc(generated))


def main():
    parser = argparse.ArgumentParser(
        description="Gera relatório de compliance profissional para vídeo, offline."
    )
    parser.add_argument("--case", required=True, type=Path, action="append",
                        help="Case JSON; repita --case para comparar dois cenários.")
    parser.add_argument("--output", type=Path, default=None,
                        help="HTML de saída; padrão: cases/DEMO-CASE-... ou DEMO-PoC3-COMPARATIVO.html.")
    args = parser.parse_args()
    cases = []
    for path in args.case:
        if not path.is_file():
            parser.error(f"Arquivo não encontrado: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            parser.error(f"Case inválido {path}: {exc}")
        if not isinstance(data, dict):
            parser.error(f"Esperado objeto JSON em {path}")
        cases.append(data)

    if args.output:
        dest = args.output
    elif len(cases) == 1:
        dest = args.case[0].parent / ("DEMO-" + args.case[0].stem + ".html")
    else:
        dest = args.case[0].parent / "DEMO-PoC3-COMPARATIVO.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render_document(cases), encoding="utf-8")
    print(f"Relatório gerado: {dest}")
    print(f"Cenários incluídos: {len(cases)}")
    print("Abra o HTML local no navegador. Use as abas para alternar os casos.")
    print("Modo apresentação: botão no cabeçalho. Teclas ←/→: mudar de caso.")
    print("Nenhuma chamada à API, atualização da blockchain ou decisão foi executada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
