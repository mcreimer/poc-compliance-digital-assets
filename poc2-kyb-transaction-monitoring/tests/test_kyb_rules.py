import unittest

from kyb_model import CompanyProfile
from kyb_rules import assess_company


def profile_row(**overrides):
    row = {
        "entityId": "TEST_COMPANY",
        "legalName": "Test Company Ltda.",
        "entityType": "company",
        "country": "BRA",
        "wallet": "0x1111111111111111111111111111111111111111",
        "registrationStatus": "ACTIVE",
        "businessActivity": "software",
        "businessRisk": "LOW",
        "highRiskJurisdiction": False,
        "adverseMedia": False,
        "documentsComplete": True,
        "sourceOfFundsVerified": True,
        "ubos": [
            {
                "uboId": "UBO_01",
                "name": "Owner One",
                "ownershipPct": 100,
                "country": "BRA",
                "pep": False,
                "sanctionsMatch": False,
                "adverseMedia": False,
            }
        ],
    }
    row.update(overrides)
    return row


class KYBRulesTest(unittest.TestCase):
    def test_clean_company_is_approved(self):
        result = assess_company(CompanyProfile.from_dict(profile_row()))
        self.assertEqual(result.corporate_risk_score, 0)
        self.assertEqual(result.status.value, "APPROVED")
        self.assertEqual(result.risk_level.value, "LOW")

    def test_fintech_delta_profile_requires_edd_with_score_35(self):
        row = profile_row(
            entityId="FINTECH_DELTA",
            businessActivity="digital asset services",
            businessRisk="MEDIUM",
            ubos=[
                {
                    "uboId": "UBO_DELTA_01",
                    "name": "Demo UBO One",
                    "ownershipPct": 70,
                    "country": "BRA",
                    "pep": False,
                    "sanctionsMatch": False,
                    "adverseMedia": False,
                },
                {
                    "uboId": "UBO_DELTA_02",
                    "name": "Demo UBO Two",
                    "ownershipPct": 30,
                    "country": "BRA",
                    "pep": True,
                    "sanctionsMatch": False,
                    "adverseMedia": False,
                },
            ],
        )
        result = assess_company(CompanyProfile.from_dict(row))
        self.assertEqual(result.corporate_risk_score, 35)
        self.assertEqual(result.status.value, "EDD_REQUIRED")
        self.assertIn("UBO_PEP", [f.rule for f in result.findings])

    def test_sanctions_match_is_hard_reject(self):
        row = profile_row(
            ubos=[
                {
                    "uboId": "UBO_01",
                    "name": "Owner One",
                    "ownershipPct": 100,
                    "country": "BRA",
                    "pep": False,
                    "sanctionsMatch": True,
                    "adverseMedia": False,
                }
            ]
        )
        result = assess_company(CompanyProfile.from_dict(row))
        self.assertEqual(result.status.value, "REJECTED")
        self.assertEqual(result.risk_level.value, "CRITICAL")
        self.assertTrue(any(f.hard_reject for f in result.findings))

    def test_ownership_must_total_100(self):
        row = profile_row(
            ubos=[
                {
                    "uboId": "UBO_01",
                    "name": "Owner One",
                    "ownershipPct": 60,
                    "country": "BRA",
                }
            ]
        )
        with self.assertRaises(ValueError):
            CompanyProfile.from_dict(row)


if __name__ == "__main__":
    unittest.main()
