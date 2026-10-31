#!/usr/bin/env python3
"""Avalia perfis corporativos KYB e apresenta uma decisão explicável."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kyb_model import CompanyProfile
from kyb_rules import assess_company


BASE = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE / "data" / "kyb_profiles.example.json"
DEFAULT_OUTPUT = BASE / "cases" / "kyb"

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


def load_profiles(path: Path) -> list[CompanyProfile]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [CompanyProfile.from_dict(row) for row in data.get("entities", [])]


def print_assessment(assessment) -> None:
    print("\n============================================")
    print(" AVALIAÇÃO DE RISCO CORPORATIVO - KYB")
    print("============================================")
    print(f"Empresa:           {assessment.legal_name}")
    print(f"ID da entidade:    {assessment.entity_id}")
    print(f"Wallet:            {assessment.wallet}")
    print(f"Score corporativo: {assessment.corporate_risk_score} / 100")
    print(
        f"Nível de risco:    "
        f"{RISK_PT.get(assessment.risk_level.value, assessment.risk_level.value)}"
    )
    print(
        f"Status KYB:        "
        f"{STATUS_PT.get(assessment.status.value, assessment.status.value)}"
    )

    print("\nRISCO DOS UBOs")
    print("--------------------------------------------")
    for ubo in assessment.ubo_risk:
        signals = ", ".join(ubo["signals"]) or "nenhum"
        nivel = RISK_PT.get(ubo["riskLevel"], ubo["riskLevel"])
        print(
            f" - {ubo['name']}: {ubo['ownershipPct']:.1f}% | "
            f"{nivel} | sinais: {signals}"
        )

    print("\nACHADOS")
    print("--------------------------------------------")
    if not assessment.findings:
        print(" - Nenhum indicador adicional de risco.")
    else:
        for finding in assessment.findings:
            reject = " [REJEIÇÃO AUTOMÁTICA]" if finding.hard_reject else ""
            print(
                f" - {finding.rule}: +{finding.points} | "
                f"{finding.evidence}{reject}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Avalia um perfil KYB corporativo com regras explicáveis."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Arquivo JSON de KYB (padrão: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--entity",
        help="entityId a avaliar. Se omitido, avalia todas as empresas.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Salva cada avaliação em JSON dentro de cases/kyb/.",
    )
    args = parser.parse_args()

    profiles = load_profiles(args.input)

    if args.entity:
        profiles = [p for p in profiles if p.entity_id == args.entity]
        if not profiles:
            raise SystemExit(f"Entidade não encontrada: {args.entity}")

    for profile in profiles:
        assessment = assess_company(profile)
        print_assessment(assessment)

        if args.save:
            DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
            output = DEFAULT_OUTPUT / f"KYB-{profile.entity_id}.json"
            with output.open("w", encoding="utf-8") as f:
                json.dump(assessment.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\nAvaliação salva em: {output}")


if __name__ == "__main__":
    main()
