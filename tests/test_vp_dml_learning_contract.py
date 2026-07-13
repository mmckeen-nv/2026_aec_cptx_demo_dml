from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPO_ROOT / "demos" / "virtual_production_studio"


class DmlLearningContractTests(unittest.TestCase):
    def test_operator_contract_requires_attempt_learning(self):
        contract = (DEMO_ROOT / "AGENTS.md").read_text()
        self.assertIn("05_dml_learning_contract.md", contract)
        self.assertIn("FAILURE_PARTIAL_MUTATION", contract)
        self.assertIn("Do not repeat an unchanged approach", contract)

    def test_learning_contract_records_and_retrieves_failures(self):
        contract = (DEMO_ROOT / "prompts" / "05_dml_learning_contract.md").read_text()
        for required in (
            "approach_signature",
            "SUCCESS_VALIDATED",
            "FAILURE_VALIDATED",
            "FAILURE_PARTIAL_MUTATION",
            "files >= 1",
            "Two failures with the same approach signature",
        ):
            self.assertIn(required, contract)

    def test_seed_knowledge_contains_success_and_failure(self):
        knowledge = DEMO_ROOT / "knowledge" / "dml"
        success = (knowledge / "rhino_massing_success_20260713.md").read_text()
        failure = (knowledge / "rhino_to_blender_obj_failure_20260713.md").read_text()
        self.assertIn("outcome: SUCCESS_VALIDATED", success)
        self.assertIn("outcome: FAILURE_PARTIAL_MUTATION", failure)
        self.assertIn("cumulative vertex offsets", failure)

    def test_direct_3dm_handoff_is_authoritative(self):
        contract = (DEMO_ROOT / "AGENTS.md").read_text()
        workflow = (DEMO_ROOT / "prompts" / "00_workflow_and_dml.md").read_text()
        importer = (REPO_ROOT / "skills" / "import_with_metadata.py").read_text()
        self.assertIn("system_prompts/07_phase_export_blender.md", contract)
        self.assertIn("IncludeRenderMeshes=true", contract)
        self.assertIn("OBJ and FBX are prohibited", workflow)
        self.assertNotIn("ToFloatArray", importer)
        self.assertNotIn("ToIntArray", importer)
        self.assertIn("unit_scale_to_meters", importer)

        knowledge = DEMO_ROOT / "knowledge" / "dml"
        success = (knowledge / "rhino_to_blender_3dm_success_20260713.md").read_text()
        regression = (knowledge / "rhino_blender_handoff_regression_20260713.md").read_text()
        self.assertIn("outcome: SUCCESS_VALIDATED", success)
        self.assertIn("outcome: FAILURE_VALIDATED", regression)


if __name__ == "__main__":
    unittest.main()
