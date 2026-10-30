#!/usr/bin/env python3
"""Explainable corporate-risk rules for the KYB PoC."""

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
        signals.append("SANCTIONS_MATCH")
        level = RiskLevel.CRITICAL
    elif ubo.pep or ubo.adverse_media:
        if ubo.pep:
            signals.append("PEP")
        if ubo.adverse_media:
            signals.append("ADVERSE_MEDIA")
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
            "REGISTRATION_NOT_ACTIVE",
            100,
            f"Company registration status is {profile.registration_status}.",
            hard_reject=True,
        )

    if profile.business_risk == BusinessRisk.MEDIUM:
        add(
            "MEDIUM_RISK_BUSINESS",
            5,
            f"Business activity '{profile.business_activity}' is classified MEDIUM for this PoC.",
        )
    elif profile.business_risk == BusinessRisk.HIGH:
        add(
            "HIGH_RISK_BUSINESS",
            20,
            f"Business activity '{profile.business_activity}' is classified HIGH for this PoC.",
        )

    if profile.high_risk_jurisdiction:
        add(
            "HIGH_RISK_JURISDICTION",
            25,
            f"Company country {profile.country} is flagged high-risk in the demonstrative dataset.",
        )

    if profile.adverse_media:
        add(
            "COMPANY_ADVERSE_MEDIA",
            25,
            "Company profile contains an adverse-media flag.",
        )

    if not profile.documents_complete:
        add(
            "DOCUMENTS_INCOMPLETE",
            30,
            "Required KYB documents are incomplete.",
        )

    if not profile.source_of_funds_verified:
        add(
            "SOURCE_OF_FUNDS_UNVERIFIED",
            20,
            "Source of funds has not been verified.",
        )

    for ubo in profile.ubos:
        if ubo.sanctions_match:
            add(
                "UBO_SANCTIONS_MATCH",
                100,
                f"{ubo.name} ({ubo.ownership_pct:.1f}% ownership) has a sanctions match.",
                subject=ubo.ubo_id,
                hard_reject=True,
            )

        if ubo.pep:
            add(
                "UBO_PEP",
                30,
                f"{ubo.name} ({ubo.ownership_pct:.1f}% ownership) is flagged as PEP.",
                subject=ubo.ubo_id,
            )

        if ubo.adverse_media:
            add(
                "UBO_ADVERSE_MEDIA",
                20,
                f"{ubo.name} ({ubo.ownership_pct:.1f}% ownership) has an adverse-media flag.",
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
