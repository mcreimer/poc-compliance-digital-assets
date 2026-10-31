#!/usr/bin/env python3
"""Regras stateful de monitoramento transacional para a PoC 2.

Os pesos, janelas de tempo e thresholds são demonstrativos e não representam
requisitos regulatórios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


JANELA_ESTRUTURACAO_MINUTOS = 30
LIMITE_ESTRUTURACAO_ETH = 10.0
JANELA_PASSAGEM_RAPIDA_MINUTOS = 15
RATIO_PASSAGEM_RAPIDA = 0.75


@dataclass(frozen=True)
class TransactionEvent:
    indice: int
    offset_minutos: int
    origem: str
    destino: str
    valor_eth: float

    @classmethod
    def from_dict(cls, indice: int, row: dict[str, Any]) -> "TransactionEvent":
        return cls(
            indice=indice,
            offset_minutos=int(row["offsetMinutes"]),
            origem=row["fromEntity"],
            destino=row["toEntity"],
            valor_eth=float(row["amountEth"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "indice": self.indice,
            "offsetMinutos": self.offset_minutos,
            "origem": self.origem,
            "destino": self.destino,
            "valorEth": self.valor_eth,
        }


@dataclass(frozen=True)
class TransactionFinding:
    regra: str
    pontos: int
    evidencia: str
    transacoes_relacionadas: tuple[int, ...]
    categoria: str = "TRANSACIONAL"

    def to_dict(self) -> dict[str, Any]:
        return {
            "regra": self.regra,
            "pontos": self.pontos,
            "evidencia": self.evidencia,
            "categoria": self.categoria,
            "transacoesRelacionadas": list(self.transacoes_relacionadas),
        }


@dataclass(frozen=True)
class TransactionAssessment:
    score_transacional: int
    score_combinado: int
    nivel_risco: str
    decisao: str
    findings: tuple[TransactionFinding, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scoreRiscoTransacional": self.score_transacional,
            "scoreRiscoCombinado": self.score_combinado,
            "nivelRiscoCombinado": self.nivel_risco,
            "decisao": self.decisao,
            "alertas": [item.to_dict() for item in self.findings],
        }


def _detectar_estruturacao(
    eventos: list[TransactionEvent],
    entidade: str,
) -> TransactionFinding | None:
    entradas = sorted(
        [
            evento
            for evento in eventos
            if evento.destino == entidade
            and evento.valor_eth < LIMITE_ESTRUTURACAO_ETH
        ],
        key=lambda item: item.offset_minutos,
    )

    melhor_janela: list[TransactionEvent] = []
    melhor_total = 0.0

    for inicio, primeiro in enumerate(entradas):
        janela = [
            evento
            for evento in entradas[inicio:]
            if evento.offset_minutos - primeiro.offset_minutos
            <= JANELA_ESTRUTURACAO_MINUTOS
        ]
        total = sum(evento.valor_eth for evento in janela)

        if len(janela) >= 2 and total >= LIMITE_ESTRUTURACAO_ETH:
            if total > melhor_total:
                melhor_total = total
                melhor_janela = janela

    if not melhor_janela:
        return None

    inicio = melhor_janela[0].offset_minutos
    fim = melhor_janela[-1].offset_minutos

    return TransactionFinding(
        regra="ESTRUTURACAO",
        pontos=30,
        evidencia=(
            f"{len(melhor_janela)} entradas individuais abaixo de "
            f"{LIMITE_ESTRUTURACAO_ETH:.1f} ETH somaram {melhor_total:.2f} ETH "
            f"em {fim - inicio} minutos."
        ),
        transacoes_relacionadas=tuple(item.indice for item in melhor_janela),
    )


def _detectar_passagem_rapida(
    eventos: list[TransactionEvent],
    entidade: str,
) -> TransactionFinding | None:
    melhor: tuple[TransactionEvent, list[TransactionEvent], float, float] | None = None

    saidas = sorted(
        [evento for evento in eventos if evento.origem == entidade],
        key=lambda item: item.offset_minutos,
    )

    for saida in saidas:
        inicio_janela = saida.offset_minutos - JANELA_PASSAGEM_RAPIDA_MINUTOS
        entradas = [
            evento
            for evento in eventos
            if evento.destino == entidade
            and inicio_janela <= evento.offset_minutos <= saida.offset_minutos
        ]

        total_entradas = sum(evento.valor_eth for evento in entradas)
        if total_entradas <= 0:
            continue

        ratio = saida.valor_eth / total_entradas

        if ratio >= RATIO_PASSAGEM_RAPIDA:
            if melhor is None or ratio > melhor[2]:
                melhor = (saida, entradas, ratio, total_entradas)

    if melhor is None:
        return None

    saida, entradas, ratio, total_entradas = melhor
    relacionados = [item.indice for item in entradas] + [saida.indice]

    return TransactionFinding(
        regra="PASSAGEM_RAPIDA_DE_FUNDOS",
        pontos=25,
        evidencia=(
            f"A entidade recebeu {total_entradas:.2f} ETH e transferiu "
            f"{saida.valor_eth:.2f} ETH em até "
            f"{JANELA_PASSAGEM_RAPIDA_MINUTOS} minutos "
            f"({ratio * 100:.1f}% do valor recebido)."
        ),
        transacoes_relacionadas=tuple(relacionados),
    )


def _detectar_contraparte_alto_risco(
    eventos: list[TransactionEvent],
    entidade: str,
    contrapartes: dict[str, dict[str, Any]],
) -> TransactionFinding | None:
    for evento in sorted(eventos, key=lambda item: item.offset_minutos):
        if evento.origem != entidade:
            continue

        contraparte = contrapartes.get(evento.destino)
        if not contraparte:
            continue

        nivel = str(contraparte.get("riskLevel", "LOW")).upper()
        if nivel not in {"HIGH", "CRITICAL"}:
            continue

        nome = contraparte.get("name", evento.destino)
        motivo = contraparte.get("riskReason", "classificação de risco elevada")

        return TransactionFinding(
            regra="CONTRAPARTE_ALTO_RISCO",
            pontos=30,
            evidencia=(
                f"Saída de {evento.valor_eth:.2f} ETH para {nome}, "
                f"classificada como {nivel}. Motivo: {motivo}."
            ),
            transacoes_relacionadas=(evento.indice,),
        )

    return None


def _contexto_ubo_alto_risco(kyb_assessment) -> TransactionFinding | None:
    ubos_alto_risco = [
        item
        for item in kyb_assessment.ubo_risk
        if str(item.get("riskLevel", "")).upper() in {"HIGH", "CRITICAL"}
    ]

    if not ubos_alto_risco:
        return None

    nomes = ", ".join(item["name"] for item in ubos_alto_risco)

    return TransactionFinding(
        regra="UBO_ALTO_RISCO",
        pontos=0,
        evidencia=(
            f"O perfil KYB possui UBO classificado como risco alto/crítico: "
            f"{nomes}. Este sinal já está refletido no score corporativo."
        ),
        transacoes_relacionadas=tuple(),
        categoria="CONTEXTO_KYB",
    )


def avaliar_transacoes(
    eventos: list[TransactionEvent],
    entidade: str,
    contrapartes: dict[str, dict[str, Any]],
    kyb_assessment,
) -> TransactionAssessment:
    findings: list[TransactionFinding] = []

    for detector in (
        lambda: _detectar_estruturacao(eventos, entidade),
        lambda: _detectar_passagem_rapida(eventos, entidade),
        lambda: _detectar_contraparte_alto_risco(
            eventos,
            entidade,
            contrapartes,
        ),
        lambda: _contexto_ubo_alto_risco(kyb_assessment),
    ):
        finding = detector()
        if finding:
            findings.append(finding)

    score_transacional = min(
        100,
        sum(item.pontos for item in findings if item.categoria == "TRANSACIONAL"),
    )

    score_combinado = min(
        100,
        kyb_assessment.corporate_risk_score + score_transacional,
    )

    if score_combinado >= 80:
        nivel_risco = "CRÍTICO"
        decisao = "ESCALAR_CASO"
    elif score_combinado >= 60:
        nivel_risco = "ALTO"
        decisao = "REVISÃO_REFORÇADA"
    elif score_combinado >= 30:
        nivel_risco = "MÉDIO"
        decisao = "MONITORAR"
    else:
        nivel_risco = "BAIXO"
        decisao = "PERMITIR"

    return TransactionAssessment(
        score_transacional=score_transacional,
        score_combinado=score_combinado,
        nivel_risco=nivel_risco,
        decisao=decisao,
        findings=tuple(findings),
    )
