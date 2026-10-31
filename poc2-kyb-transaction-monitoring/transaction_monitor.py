#!/usr/bin/env python3
"""Executa o cenário demonstrativo de KYB + Transaction Monitoring."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path

from kyb_model import CompanyProfile
from kyb_rules import assess_company
from transaction_rules import (
    JANELA_ESTRUTURACAO_MINUTOS,
    JANELA_PASSAGEM_RAPIDA_MINUTOS,
    LIMITE_ESTRUTURACAO_ETH,
    RATIO_PASSAGEM_RAPIDA,
    TransactionEvent,
    avaliar_transacoes,
)


BASE = Path(__file__).resolve().parent
DEFAULT_SCENARIO = BASE / "data" / "transaction_scenario.example.json"
DEFAULT_KYB = BASE / "data" / "kyb_profiles.example.json"
DEFAULT_COUNTERPARTIES = BASE / "data" / "counterparties.example.json"
DEFAULT_CASES = BASE / "cases" / "monitoramento"


RISK_PT = {
    "LOW": "BAIXO",
    "MEDIUM": "MÉDIO",
    "HIGH": "ALTO",
    "CRITICAL": "CRÍTICO",
}

STATUS_PT = {
    "APPROVED": "APROVADO",
    "EDD_REQUIRED": "EDD NECESSÁRIA",
    "REJECTED": "REJEITADO",
}


def carregar_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def carregar_perfil_kyb(path: Path, entity_id: str) -> CompanyProfile:
    data = carregar_json(path)

    for row in data.get("entities", []):
        if row.get("entityId") == entity_id:
            return CompanyProfile.from_dict(row)

    raise ValueError(f"Entidade não encontrada no arquivo KYB: {entity_id}")


def carregar_contrapartes(path: Path) -> dict[str, dict]:
    data = carregar_json(path)
    return {
        item["entityId"]: item
        for item in data.get("counterparties", [])
    }


def formatar_horario(base_time: datetime, offset_minutos: int) -> str:
    return (base_time + timedelta(minutes=offset_minutos)).strftime("%H:%M")


def imprimir_cabecalho(scenario: dict, profile, kyb_assessment) -> None:
    print("\n============================================================")
    print(" MONITORAMENTO DE TRANSAÇÕES DE ATIVOS DIGITAIS")
    print("============================================================")
    print(f"Cenário:          {scenario['scenarioId']}")
    print(f"Entidade:         {profile.legal_name}")
    print(f"Entity ID:        {profile.entity_id}")
    print(f"Wallet:           {profile.wallet}")
    print()
    print("PERFIL KYB")
    print("------------------------------------------------------------")
    print(
        f"Score corporativo: {kyb_assessment.corporate_risk_score} / 100"
    )
    print(
        f"Nível de risco:    "
        f"{RISK_PT.get(kyb_assessment.risk_level.value, kyb_assessment.risk_level.value)}"
    )
    print(
        f"Status KYB:        "
        f"{STATUS_PT.get(kyb_assessment.status.value, kyb_assessment.status.value)}"
    )


def imprimir_eventos(
    scenario: dict,
    eventos: list[TransactionEvent],
) -> None:
    base_time = datetime.fromisoformat(scenario["baseTime"])

    print("\nMOVIMENTAÇÕES ANALISADAS")
    print("------------------------------------------------------------")

    for evento in sorted(eventos, key=lambda item: item.offset_minutos):
        horario = formatar_horario(base_time, evento.offset_minutos)
        print(
            f"[{evento.indice}] {horario}  "
            f"{evento.origem} -> {evento.destino}  "
            f"{evento.valor_eth:.2f} ETH"
        )


def imprimir_resultado(assessment) -> None:
    print("\nALERTAS E CONTEXTO DETECTADOS")
    print("------------------------------------------------------------")

    for finding in assessment.findings:
        pontos = f"+{finding.pontos}" if finding.pontos else "contexto"
        print(f"[{finding.regra}] {pontos}")
        print(f"  {finding.evidencia}")

    print("\nRESULTADO CONSOLIDADO")
    print("------------------------------------------------------------")
    print(f"Score transacional: {assessment.score_transacional} / 100")
    print(f"Score combinado:    {assessment.score_combinado} / 100")
    print(f"Nível de risco:     {assessment.nivel_risco}")
    print(f"Decisão:            {assessment.decisao}")

    if assessment.decisao == "ESCALAR_CASO":
        print("\n>>> CASO DE COMPLIANCE DEVE SER ESCALADO PARA INVESTIGAÇÃO <<<")


def construir_case(
    scenario: dict,
    profile,
    kyb_assessment,
    eventos: list[TransactionEvent],
    assessment,
) -> dict:
    base_time = datetime.fromisoformat(scenario["baseTime"])

    transacoes = []
    for evento in sorted(eventos, key=lambda item: item.offset_minutos):
        row = evento.to_dict()
        row["horario"] = (
            base_time + timedelta(minutes=evento.offset_minutos)
        ).isoformat()
        transacoes.append(row)

    return {
        "idCaso": f"CASO-{scenario['scenarioId']}",
        "cenario": {
            "id": scenario["scenarioId"],
            "descricao": scenario.get("description", ""),
            "dataHoraBase": scenario["baseTime"],
        },
        "entidade": {
            "entityId": profile.entity_id,
            "razaoSocial": profile.legal_name,
            "wallet": profile.wallet,
        },
        "perfilKyb": {
            "scoreRiscoCorporativo": kyb_assessment.corporate_risk_score,
            "nivelRisco": RISK_PT.get(
                kyb_assessment.risk_level.value,
                kyb_assessment.risk_level.value,
            ),
            "status": STATUS_PT.get(
                kyb_assessment.status.value,
                kyb_assessment.status.value,
            ),
            "achados": [
                item.to_dict() for item in kyb_assessment.findings
            ],
            "ubos": list(kyb_assessment.ubo_risk),
        },
        "transacoesRelacionadas": transacoes,
        "monitoramento": assessment.to_dict(),
        "parametros": {
            "limiteEstruturacaoEth": LIMITE_ESTRUTURACAO_ETH,
            "janelaEstruturacaoMinutos": JANELA_ESTRUTURACAO_MINUTOS,
            "janelaPassagemRapidaMinutos": JANELA_PASSAGEM_RAPIDA_MINUTOS,
            "ratioPassagemRapida": RATIO_PASSAGEM_RAPIDA,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Executa uma análise demonstrativa combinando KYB e "
            "monitoramento transacional."
        )
    )
    parser.add_argument(
        "--cenario",
        type=Path,
        default=DEFAULT_SCENARIO,
        help="Arquivo JSON com o cenário transacional.",
    )
    parser.add_argument(
        "--kyb",
        type=Path,
        default=DEFAULT_KYB,
        help="Arquivo JSON com os perfis KYB.",
    )
    parser.add_argument(
        "--contrapartes",
        type=Path,
        default=DEFAULT_COUNTERPARTIES,
        help="Arquivo JSON com inteligência de contrapartes.",
    )
    parser.add_argument(
        "--salvar",
        action="store_true",
        help="Salva o caso consolidado em JSON.",
    )
    args = parser.parse_args()

    scenario = carregar_json(args.cenario)
    entity_id = scenario["subjectEntity"]

    profile = carregar_perfil_kyb(args.kyb, entity_id)
    kyb_assessment = assess_company(profile)
    contrapartes = carregar_contrapartes(args.contrapartes)

    eventos = [
        TransactionEvent.from_dict(indice, row)
        for indice, row in enumerate(scenario.get("events", []), start=1)
    ]

    assessment = avaliar_transacoes(
        eventos=eventos,
        entidade=entity_id,
        contrapartes=contrapartes,
        kyb_assessment=kyb_assessment,
    )

    imprimir_cabecalho(scenario, profile, kyb_assessment)
    imprimir_eventos(scenario, eventos)
    imprimir_resultado(assessment)

    if args.salvar:
        DEFAULT_CASES.mkdir(parents=True, exist_ok=True)
        output = DEFAULT_CASES / f"CASO-{scenario['scenarioId']}.json"
        case = construir_case(
            scenario,
            profile,
            kyb_assessment,
            eventos,
            assessment,
        )
        with output.open("w", encoding="utf-8") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)

        print(f"\nCaso salvo em: {output}")


if __name__ == "__main__":
    main()
