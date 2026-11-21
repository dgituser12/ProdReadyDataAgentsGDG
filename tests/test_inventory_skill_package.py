import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "inventory-risk-analysis"

class InventorySkillPackageTests(unittest.TestCase):
    def test_skill_and_references_exist(self):
        self.assertTrue((SKILL / "SKILL.md").is_file())
        self.assertTrue((SKILL / "references" / "inventory-glossary.md").is_file())
        self.assertTrue((SKILL / "references" / "risk-scoring-guide.md").is_file())

    def test_skill_preserves_read_only_and_financial_guardrails(self):
        text = (SKILL / "SKILL.md").read_text().lower()
        self.assertIn("read-only", text)
        self.assertIn("not lost sales", text)
        self.assertIn("supplier profile risk tier", text)

    def test_risk_guide_does_not_claim_canonical_numeric_score(self):
        text = (SKILL / "references" / "risk-scoring-guide.md").read_text()
        self.assertIn("does not define a canonical numeric composite risk score", text)

    def test_all_domain_skill_packages_exist_and_are_read_only(self):
        for name in ("supplier-performance-analysis", "fulfilment-exposure-analysis"):
            skill_file = ROOT / "skills" / name / "SKILL.md"
            self.assertTrue(skill_file.is_file())
            text = skill_file.read_text().lower()
            self.assertIn("read-only", text)

if __name__ == "__main__":
    unittest.main()
