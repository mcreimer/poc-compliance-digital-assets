#!/usr/bin/env python3
"""Offline unit tests: no Besu node, credentials or Sumsub network required."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import send_to_sumsub
import compliance_monitor
import sumsub_tm_case
import review_sumsub_tm
import demo_case_report


HASH = "0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c"


class SumsubTMTests(unittest.TestCase):
    def test_existing_applicant_mapping(self):
        with tempfile.TemporaryDirectory() as folder:
            mapping = [{
                "entityId": "BANK_ALPHA",
                "applicantId": "TESTSANDBOXAPPLICANT001",
            }]
            (Path(folder) / "sumsub_applicants.json").write_text(
                json.dumps(mapping), encoding="utf-8"
            )
            with patch.object(send_to_sumsub, "BASE", Path(folder)):
                actual = send_to_sumsub.existing_applicant_id({"id": "BANK_ALPHA"})
            self.assertEqual(actual, "TESTSANDBOXAPPLICANT001")

    def test_case_preserves_independent_local_score(self):
        with tempfile.TemporaryDirectory() as folder:
            cases = Path(folder) / "cases"
            cases.mkdir()
            target = cases / "CASE-CF85CF6D.json"
            target.write_text(json.dumps({
                "caseId": "CASE-CF85CF6D",
                "transaction": {"hash": HASH},
                "riskAssessment": {"score": 60, "decision": "MANUAL_REVIEW"},
            }), encoding="utf-8")
            tm_response = {
                "id": "testInternalId",
                "data": {"txnId": "besu" + HASH[2:]},
                "scoringResult": {"score": 30, "matchedRules": [{
                    "name": "Sandbox amount rule",
                    "score": 30,
                }]},
                "review": {"reviewStatus": "onHold"},
            }
            with patch.object(sumsub_tm_case, "BASE", Path(folder)):
                path = sumsub_tm_case.save_sumsub_result(
                    HASH, tm_response, applicant_id="TESTSANDBOXAPPLICANT001",
                    stage="submitted"
                )
            result = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(result["riskAssessment"]["score"], 60)
            self.assertEqual(result["sumsubTransactionMonitoring"]["score"], 30)
            self.assertEqual(
                result["sumsubTransactionMonitoring"]["reviewStatus"], "onHold"
            )
            self.assertEqual(
                len(result["sumsubTransactionMonitoring"]["matchedRules"]), 1
            )

    def test_refresh_local_assessment_preserves_sumsub_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            cases = Path(folder) / "cases"
            cases.mkdir()
            target = cases / "CASE-CF85CF6D.json"
            provider_evidence = {
                "score": 60,
                "reviewStatus": "onHold",
                "matchedRules": [{"name": "POC3 - Transferencia de alto valor de ETH"}],
            }
            target.write_text(json.dumps({
                "caseId": "CASE-CF85CF6D",
                "createdAt": "2026-11-03T18:00:00+00:00",
                "transaction": {"hash": HASH},
                "sumsubTransactionMonitoring": provider_evidence,
                "riskAssessment": {"score": 30},
            }), encoding="utf-8")

            revised_local = {
                "caseId": "CASE-CF85CF6D",
                "createdAt": "2026-11-03T19:00:00+00:00",
                "transaction": {"hash": HASH, "amount": 11.0},
                "riskAssessment": {"score": 60, "decision": "MANUAL_REVIEW"},
            }
            path = compliance_monitor.save_case_preserving_provider_evidence(
                revised_local, base_dir=Path(folder)
            )
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(saved["riskAssessment"]["score"], 60)
            self.assertEqual(saved["sumsubTransactionMonitoring"], provider_evidence)
            self.assertEqual(saved["transaction"]["amount"], 11.0)
            self.assertEqual(saved["createdAt"], "2026-11-03T18:00:00+00:00")

    def test_provider_timeline_preserves_on_hold_before_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)
            provider_on_hold = {
                "id": "TESTTXN123456",
                "data": {"txnId": "besu" + HASH[2:]},
                "scoringResult": {"score": 60, "matchedRules": [
                    {"name": "POC3 - Transferencia de alto valor de ETH"}
                ]},
                "review": {"reviewStatus": "onHold"},
            }
            provider_completed = {
                **provider_on_hold,
                "review": {"reviewStatus": "completed",
                           "reviewResult": {"reviewAnswer": "GREEN"}},
            }
            with patch.object(sumsub_tm_case, "BASE", p):
                sumsub_tm_case.save_sumsub_result(
                    HASH, provider_on_hold, stage="queried"
                )
                path = sumsub_tm_case.save_sumsub_result(
                    HASH, provider_completed, stage="manual-decision-confirmed"
                )
            saved = json.loads(path.read_text(encoding="utf-8"))
            states = [x["reviewStatus"] for x in
                      saved["sumsubMonitoringTimeline"]]
            self.assertEqual(states, ["onHold", "completed"])
            self.assertEqual(
                saved["sumsubTransactionMonitoring"]["reviewAnswer"], "GREEN"
            )

    def test_review_decision_requires_exact_identity_and_onhold(self):
        target = "besu" + HASH[2:]
        valid = {
            "id": "TESTTXN123456",
            "data": {"txnId": target},
            "review": {"reviewStatus": "onHold"},
        }
        review_sumsub_tm.validate_decision(
            target, valid, "TESTTXN123456", "approve"
        )
        with self.assertRaises(ValueError):
            review_sumsub_tm.validate_decision(
                target, valid, "WRONGTXN123456", "approve"
            )
        with self.assertRaises(ValueError):
            review_sumsub_tm.validate_decision(
                target, {**valid, "review": {"reviewStatus": "completed"}},
                "TESTTXN123456", "reject"
            )
        with self.assertRaises(ValueError):
            review_sumsub_tm.validate_decision(
                "besu" + ("0" * 64), valid, "TESTTXN123456", "approve"
            )

    def test_report_two_cases_and_statuses_without_leaking_full_api(self):
        original = {
            "caseId": "CASE-CF85CF6D",
            "transaction": {"hash": HASH, "amount": 11.0, "block": 4453, "status": 1},
            "sender": {"name": "Banco Alpha"},
            "counterparty": {"name": "Custodian Gamma"},
            "network": {"chainId": 1337},
            "riskAssessment": {"score": 60, "decision": "MANUAL_REVIEW"},
            "sumsubTransactionMonitoring": {
                "score": 60,
                "reviewStatus": "onHold",
                "reviewAnswer": None,
                "matchedRules": [{"name": "POC3 - Transferencia de alto valor de ETH"}],
                "response": {"secret": "API_RESPONSE_SHOULD_NOT_APPEAR"},
            },
            "sumsubMonitoringTimeline": [
                {"reviewStatus": "onHold", "score": 60,
                 "observedAt": "2026-11-03T15:00:00+00:00"},
            ],
        }
        second = {
            **original,
            "caseId": "CASE-54494580",
            "transaction": {"hash": "0x" + ("1" * 64), "amount": 12.0, "block": 27683,
                            "status": 1},
            "sumsubTransactionMonitoring": {
                "score": 60, "reviewStatus": "completed", "reviewAnswer": "GREEN",
                "matchedRules": [{"name": "POC3 - Transferencia de alto valor de ETH"}],
            },
            "sumsubMonitoringTimeline": [
                {"reviewStatus": "onHold", "score": 60,
                 "observedAt": "2026-11-03T15:00:00+00:00"},
                {"reviewStatus": "completed", "reviewAnswer": "GREEN", "score": 60,
                 "observedAt": "2026-11-03T16:00:00+00:00"},
            ],
        }
        page = demo_case_report.render_document([original, second])
        self.assertIn("CASE-CF85CF6D", page)
        self.assertIn("CASE-54494580", page)
        self.assertIn("Aguardando revisão", page)
        self.assertIn("Aprovada manualmente", page)
        self.assertIn("POC3 - Transferencia", page)
        self.assertIn("data-target=\"1\"", page)
        self.assertNotIn("API_RESPONSE_SHOULD_NOT_APPEAR", page)

    def test_report_escapes_untrusted_case_text(self):
        case = {
            "caseId": "CASE-00000000",
            "transaction": {"hash": "<script>danger</script>", "amount": 1},
            "sender": {"name": "<img src=x onerror=alert(1)>"},
            "sumsubTransactionMonitoring": {
                "score": 0, "reviewStatus": "onHold",
                "matchedRules": [{"name": "<b>Not a title</b>"}],
            },
        }
        page = demo_case_report.render_document([case])
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", page)
        self.assertIn("&lt;b&gt;Not a title&lt;/b&gt;", page)
        self.assertNotIn("<img src=x onerror=alert(1)>", page)

    def test_case_rejects_different_transaction(self):
        with tempfile.TemporaryDirectory() as folder:
            cases = Path(folder) / "cases"
            cases.mkdir()
            (cases / "CASE-CF85CF6D.json").write_text(
                json.dumps({"transaction": {"hash": "0x" + ("0" * 64)}}),
                encoding="utf-8",
            )
            with patch.object(sumsub_tm_case, "BASE", Path(folder)):
                with self.assertRaises(ValueError):
                    sumsub_tm_case.save_sumsub_result(HASH, {})


if __name__ == "__main__":
    unittest.main()
