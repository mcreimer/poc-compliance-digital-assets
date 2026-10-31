#!/usr/bin/env python3
"""Regras explicáveis de risco corporativo para a PoC de KYB."""

from __future__ import annotations

from kyb_model import (
    BusinessRisk,
    CompanyProfile,
    KYBAssessment,
    KYBStatus,
    RiskFinding,
    RiskLevel,
    UBO,
)


def _ubo_risk(ubo: UBO) -> dict:
    signals = []

    if ubo.sanctions_match:
        signals.append("LISTA_SANCOES")
        level = RiskLevel.CRITICAL
    elif ubo.pep or ubo.adverse_media:
        if ubo.pep:
            signals.append("PEP")
        if ubo.adverse_media:
            signals.append("MIDIA_ADVERSA")
        level = RiskLevel.HIGH
    else:
        level = RiskLevel.LOW

    return {
        "uboId": ubo.ubo_id,
        "name": ubo.name,
        "ownershipPct": ubo.ownership_pct,
        "riskLevel": level.value,
        "signals": signals,
    }


def assess_company(profile: CompanyProfile) -> KYBAssessment:
    findings: list[RiskFinding] = []

    def add(
        rule: str,
        points: int,
        evidence: str,
        subject: str | None = None,
        hard_reject: bool = False,
    ) -> None:
        findings.append(
            RiskFinding(
                rule=rule,
                points=points,
                evidence=evidence,
                subject=subject or profile.entity_id,
                hard_reject=hard_reject,
            )
        )

    if profile.registration_status.upper() != "ACTIVE":
        add(
            "REGISTRO_EMPRESA_INATIVO",
            100,
            f"O status cadastral da empresa é {profile.registration_status}.",
            hard_reject=True,
        )

    if profile.business_risk == BusinessRisk.MEDIUM:
        add(
            "NEGOCIO_RISCO_MEDIO",
            5,
            (
                f"A atividade '{profile.business_activity}' foi classificada "
                "como risco médio neste cenário demonstrativo."
            ),
        )
    elif profile.business_risk == BusinessRisk.HIGH:
        add(
            "NEGOCIO_ALTO_RISCO",
            20,
            (
                f"A atividade '{profile.business_activity}' foi classificada "
                "como alto risco neste cenário demonstrativo."
            ),
        )

    if profile.high_risk_jurisdiction:
        add(
            "JURISDICAO_ALTO_RISCO",
            25,
            (
                f"O país {profile.country} está marcado como jurisdição de "
                "alto risco no dataset demonstrativo."
            ),
        )

    if profile.adverse_media:
        add(
            "MIDIA_ADVERSA_EMPRESA",
            25,
            "O perfil da empresa possui indicador de mídia adversa.",
        )

    if not profile.documents_complete:
        add(
            "DOCUMENTOS_INCOMPLETOS",
            30,
            "Os documentos requeridos para KYB estão incompletos.",
        )

    if not profile.source_of_funds_verified:
        add(
            "ORIGEM_RECURSOS_NAO_VERIFICADA",
            20,
            "A origem dos recursos ainda não foi verificada.",
        )

    for ubo in profile.ubos:
        if ubo.sanctions_match:
            add(
                "UBO_LISTA_SANCOES",
                100,
                (
                    f"{ubo.name} ({ubo.ownership_pct:.1f}% de participação) "
                    "possui correspondência em lista de sanções."
                ),
                subject=ubo.ubo_id,
                hard_reject=True,
            )

        if ubo.pep:
            add(
                "UBO_PEP",
                30,
                (
                    f"{ubo.name} ({ubo.ownership_pct:.1f}% de participação) "
                    "está sinalizado como PEP."
                ),
                subject=ubo.ubo_id,
            )

        if ubo.adverse_media:
            add(
                "MIDIA_ADVERSA_UBO",
                20,
                (
                    f"{ubo.name} ({ubo.ownership_pct:.1f}% de participação) "
                    "possui indicador de mídia adversa."
                ),
                subject=ubo.ubo_id,
            )

    hard_reject = any(item.hard_reject for item in findings)
    score = min(100, sum(item.points for item in findings))

    if hard_reject:
        status = KYBStatus.REJECTED
        risk_level = RiskLevel.CRITICAL
    elif score >= 70:
        status = KYBStatus.REJECTED
        risk_level = RiskLevel.CRITICAL
    elif score >= 30:
        status = KYBStatus.EDD_REQUIRED
        risk_level = RiskLevel.HIGH
    elif score >= 10:
        status = KYBStatus.APPROVED
        risk_level = RiskLevel.MEDIUM
    else:
        status = KYBStatus.APPROVED
        risk_level = RiskLevel.LOW

    return KYBAssessment(
        entity_id=profile.entity_id,
        legal_name=profile.legal_name,
        wallet=profile.wallet,
        corporate_risk_score=score,
        risk_level=risk_level,
        status=status,
        findings=tuple(findings),
        ubo_risk=tuple(_ubo_risk(ubo) for ubo in profile.ubos),
    )
