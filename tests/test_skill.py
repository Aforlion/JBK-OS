import unittest

from core.skill import Skill, SkillStatus


class TestSkill(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = Skill(
            skill_id="SKL-0001",
            name="Deploy DB",
            description="Deploys database clusters",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Antigravity",
            capabilities=["db", "deployment", "postgres"],
            inputs=["spec"],
            outputs=["host"],
            version="1.0",
        )

    def test_instantiation_and_values(self) -> None:
        self.assertEqual(self.skill.skill_id, "SKL-0001")
        self.assertEqual(self.skill.name, "Deploy DB")
        self.assertEqual(self.skill.description, "Deploys database clusters")
        self.assertEqual(self.skill.owner_id, "EXEC-0002")
        self.assertEqual(self.skill.department, "Operations")
        self.assertEqual(self.skill.execution_engine, "Antigravity")
        self.assertEqual(self.skill.capabilities, ["db", "deployment", "postgres"])
        self.assertEqual(self.skill.inputs, ["spec"])
        self.assertEqual(self.skill.outputs, ["host"])
        self.assertEqual(self.skill.version, "1.0")
        self.assertEqual(self.skill.status, SkillStatus.AVAILABLE)

    def test_instantiation_raises_on_missing_args(self) -> None:
        with self.assertRaises(ValueError):
            Skill("", "Name", "Desc", "Owner", "Dept", "Engine", [], [], [], "1.0")
        with self.assertRaises(ValueError):
            Skill("SKL-0001", "", "Desc", "Owner", "Dept", "Engine", [], [], [], "1.0")
        with self.assertRaises(ValueError):
            Skill("SKL-0001", "Name", "Desc", "", "Dept", "Engine", [], [], [], "1.0")
        with self.assertRaises(ValueError):
            Skill("SKL-0001", "Name", "Desc", "Owner", "", "Engine", [], [], [], "1.0")
        with self.assertRaises(ValueError):
            Skill("SKL-0001", "Name", "Desc", "Owner", "Dept", "", [], [], [], "1.0")
        with self.assertRaises(ValueError):
            Skill("SKL-0001", "Name", "Desc", "Owner", "Dept", "Engine", [], [], [], "")

    def test_immutability(self) -> None:
        with self.assertRaises(AttributeError):
            self.skill.skill_id = "SKL-0002"
        with self.assertRaises(AttributeError):
            self.skill.name = "Rename DB"
        with self.assertRaises(AttributeError):
            self.skill.capabilities = []

    def test_supports_capability(self) -> None:
        self.assertTrue(self.skill.supports("db"))
        self.assertTrue(self.skill.supports("POSTGRES"))
        self.assertTrue(self.skill.supports(" deployment "))
        self.assertFalse(self.skill.supports("javascript"))
        self.assertFalse(self.skill.supports(""))

    def test_update_status(self) -> None:
        self.skill.update_status(SkillStatus.BUSY)
        self.assertEqual(self.skill.status, SkillStatus.BUSY)

        self.skill.update_status("DISABLED")
        self.assertEqual(self.skill.status, SkillStatus.DISABLED)

        with self.assertRaises(ValueError):
            self.skill.update_status("INVALID_STATUS")

    def test_serialization(self) -> None:
        sum_dict = self.skill.summary()
        self.assertEqual(sum_dict["skill_id"], "SKL-0001")
        self.assertEqual(sum_dict["name"], "Deploy DB")
        self.assertNotIn("execution_engine", sum_dict)

        full_dict = self.skill.to_dict()
        self.assertEqual(full_dict["execution_engine"], "Antigravity")
        self.assertEqual(full_dict["capabilities"], ["db", "deployment", "postgres"])
