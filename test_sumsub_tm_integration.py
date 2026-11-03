#!/usr/bin/env python3
"""Offline unit tests: no Besu node, credentials or Sumsub network required."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import send_to_sumsub
import sumsub_tm_case


HASH = "0xcf85cf6d25235bac271236f5a4e46290cad5c237da06f7702df07ced26fcf89c"


class SumsubTMTests(unittest.TestCase):
    def test_existing_applicant_mapping(self):
        with tempfile.TemporaryDirectory() as folder:
            mapping = [{
                "entityId": "BANK_ALPHA",
                "applicantId": "6abd2cf20b8a55780eccb1c6",
            }]
            (Path(folder) / "sumsub_applicants.json").write_text(
                json.dumps(mapping), encoding="utf-8"
            )
            with patch.object(send_to_sumsub, "BASE", Path(folder)):
                actual = send_to_sumsub.existing_applicant_id({"id": "BANK_ALPHA"})
            self.assertEqual(actual, "6abd2cf20b8a55780eccb1c6")

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
                    HASH, tm_response, applicant_id="6abd2cf20b8a55780eccb1c6",
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
