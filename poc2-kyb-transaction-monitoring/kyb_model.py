#!/usr/bin/env python3
"""Domain model and validation for the KYB PoC.

All scoring thresholds and rules in this project are demonstrative and must not
be interpreted as regulatory requirements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Any


WALLET_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


class KYBStatus(str, Enum):
    APPROVED = "APPROVED"
    EDD_REQUIRED = "EDD_REQUIRED"
    REJECTED = "REJECTED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BusinessRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class UBO:
    ubo_id: str
    name: str
    ownership_pct: float
    country: str
    pep: bool = False
    sanctions_match: bool = False
    adverse_media: bool = False

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "UBO":
        return cls(
            ubo_id=row["uboId"],
            name=row["name"],
            ownership_pct=float(row["ownershipPct"]),
            country=row.get("country", "UNK"),
            pep=bool(row.get("pep", False)),
            sanctions_match=bool(row.get("sanctionsMatch", False)),
            adverse_media=bool(row.get("adverseMedia", False)),
        )


@dataclass(frozen=True)
class CompanyProfile:
    entity_id: str
    legal_name: str
    entity_type: str
    country: str
    wallet: str
    registration_status: str
    business_activity: str
    business_risk: BusinessRisk
    high_risk_jurisdiction: bool
    adverse_media: bool
    documents_complete: bool
    source_of_funds_verified: bool
    ubos: tuple[UBO, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> "CompanyProfile":
        profile = cls(
            entity_id=row["entityId"],
            legal_name=row["legalName"],
            entity_type=row.get("entityType", "company"),
            country=row["country"],
            wallet=row["wallet"],
            registration_status=row.get("registrationStatus", "UNKNOWN"),
            business_activity=row.get("businessActivity", "UNKNOWN"),
            business_risk=BusinessRisk(row.get("businessRisk", "LOW")),
            high_risk_jurisdiction=bool(row.get("highRiskJurisdiction", False)),
            adverse_media=bool(row.get("adverseMedia", False)),
            documents_complete=bool(row.get("documentsComplete", False)),
            source_of_funds_verified=bool(row.get("sourceOfFundsVerified", False)),
            ubos=tuple(UBO.from_dict(item) for item in row.get("ubos", [])),
        )
        profile.validate()
        return profile

    def validate(self) -> None:
        if self.entity_type.lower() != "company":
            raise ValueError(f"{self.entity_id}: entityType must be 'company'")

        if not WALLET_RE.match(self.wallet):
            raise ValueError(f"{self.entity_id}: invalid Ethereum-style wallet")

        if not self.ubos:
            raise ValueError(f"{self.entity_id}: at least one UBO is required")

        seen = set()
        total = 0.0

        for ubo in self.ubos:
            if ubo.ubo_id in seen:
                raise ValueError(f"{self.entity_id}: duplicate UBO id {ubo.ubo_id}")
            seen.add(ubo.ubo_id)

            if ubo.ownership_pct <= 0 or ubo.ownership_pct > 100:
                raise ValueError(
                    f"{self.entity_id}: invalid ownership for {ubo.ubo_id}"
                )

            total += ubo.ownership_pct

        if abs(total - 100.0) > 0.01:
            raise ValueError(
                f"{self.entity_id}: ownership must total 100%, got {total:.2f}%"
            )


@dataclass(frozen=True)
class RiskFinding:
    rule: str
    points: int
    evidence: str
    subject: str
    hard_reject: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "points": self.points,
            "evidence": self.evidence,
            "subject": self.subject,
            "hardReject": self.hard_reject,
        }


@dataclass(frozen=True)
class KYBAssessment:
    entity_id: str
    legal_name: str
    wallet: str
    corporate_risk_score: int
    risk_level: RiskLevel
    status: KYBStatus
    findings: tuple[RiskFinding, ...]
    ubo_risk: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "entityId": self.entity_id,
            "legalName": self.legal_name,
            "wallet": self.wallet,
            "corporateRiskScore": self.corporate_risk_score,
            "riskLevel": self.risk_level.value,
            "kybStatus": self.status.value,
            "findings": [item.to_dict() for item in self.findings],
            "uboRisk": list(self.ubo_risk),
        }
