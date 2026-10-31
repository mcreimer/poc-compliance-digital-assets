import json
from pathlib import Path
import unittest

from kyb_model import CompanyProfile
from kyb_rules import assess_company
from transaction_rules import TransactionEvent, avaliar_transacoes


BASE = Path(__file__).resolve().parents[1]


class TransactionMonitorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (BASE / "data" / "transaction_scenario.example.json").open(
            "r", encoding="utf-8"
        ) as f:
            cls.scenario = json.load(f)

        with (BASE / "data" / "kyb_profiles.example.json").open(
            "r", encoding="utf-8"
        ) as f:
            kyb_data = json.load(f)

        with (BASE / "data" / "counterparties.example.json").open(
            "r", encoding="utf-8"
        ) as f:
            cp_data = json.load(f)

        profile_row = next(
            row
            for row in kyb_data["entities"]
            if row["entityId"] == cls.scenario["subjectEntity"]
        )

        cls.profile = CompanyProfile.from_dict(profile_row)
        cls.kyb_assessment = assess_company(cls.profile)
        cls.counterparties = {
            item["entityId"]: item for item in cp_data["counterparties"]
        }
        cls.events = [
            TransactionEvent.from_dict(index, row)
            for index, row in enumerate(cls.scenario["events"], start=1)
        ]
        cls.assessment = avaliar_transacoes(
            cls.events,
            cls.scenario["subjectEntity"],
            cls.counterparties,
            cls.kyb_assessment,
        )

    def test_detecta_estruturacao(self):
        rules = [item.regra for item in self.assessment.findings]
        self.assertIn("ESTRUTURACAO", rules)

    def test_detecta_passagem_rapida(self):
        rules = [item.regra for item in self.assessment.findings]
        self.assertIn("PASSAGEM_RAPIDA_DE_FUNDOS", rules)

    def test_detecta_contraparte_alto_risco(self):
        rules = [item.regra for item in self.assessment.findings]
        self.assertIn("CONTRAPARTE_ALTO_RISCO", rules)

    def test_inclui_contexto_ubo(self):
        rules = [item.regra for item in self.assessment.findings]
        self.assertIn("UBO_ALTO_RISCO", rules)

    def test_score_transacional_85(self):
        self.assertEqual(self.assessment.score_transacional, 85)

    def test_score_combinado_100_e_escala(self):
        self.assertEqual(self.kyb_assessment.corporate_risk_score, 35)
        self.assertEqual(self.assessment.score_combinado, 100)
        self.assertEqual(self.assessment.nivel_risco, "CRÍTICO")
        self.assertEqual(self.assessment.decisao, "ESCALAR_CASO")


if __name__ == "__main__":
    unittest.main()
