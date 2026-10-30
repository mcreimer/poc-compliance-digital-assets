#!/usr/bin/env python3
"""Evaluate corporate KYB profiles and print an explainable decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kyb_model import CompanyProfile
from kyb_rules import assess_company


BASE = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE / "data" / "kyb_profiles.example.json"
DEFAULT_OUTPUT = BASE / "cases" / "kyb"


def load_profiles(path: Path) -> list[CompanyProfile]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return [CompanyProfile.from_dict(row) for row in data.get("entities", [])]


def print_assessment(assessment) -> None:
    print("\n====================================")
    print(" CORPORATE KYB RISK ASSESSMENT")
    print("====================================")
    print(f"Entity:          {assessment.legal_name}")
    print(f"Entity ID:       {assessment.entity_id}")
    print(f"Wallet:          {assessment.wallet}")
    print(f"Corporate score: {assessment.corporate_risk_score} / 100")
    print(f"Risk level:      {assessment.risk_level.value}")
    print(f"KYB status:      {assessment.status.value}")

    print("\nUBO risk:")
    for ubo in assessment.ubo_risk:
        signals = ", ".join(ubo["signals"]) or "none"
        print(
            f" - {ubo['name']}: {ubo['ownershipPct']:.1f}% | "
            f"{ubo['riskLevel']} | signals: {signals}"
        )

    print("\nFindings:")
    if not assessment.findings:
        print(" - No risk findings.")
    else:
        for finding in assessment.findings:
            reject = " [HARD REJECT]" if finding.hard_reject else ""
            print(
                f" - {finding.rule}: +{finding.points} | "
                f"{finding.evidence}{reject}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate an explainable KYB corporate-risk profile."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"KYB JSON file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--entity",
        help="Optional entityId to evaluate. If omitted, evaluates all entities.",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save each assessment as JSON under cases/kyb/.",
    )
    args = parser.parse_args()

    profiles = load_profiles(args.input)

    if args.entity:
        profiles = [p for p in profiles if p.entity_id == args.entity]
        if not profiles:
            raise SystemExit(f"Entity not found: {args.entity}")

    for profile in profiles:
        assessment = assess_company(profile)
        print_assessment(assessment)

        if args.save:
            DEFAULT_OUTPUT.mkdir(parents=True, exist_ok=True)
            output = DEFAULT_OUTPUT / f"KYB-{profile.entity_id}.json"
            with output.open("w", encoding="utf-8") as f:
                json.dump(assessment.to_dict(), f, indent=2, ensure_ascii=False)
            print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
