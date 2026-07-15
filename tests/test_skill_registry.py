import unittest

from core.skill import Skill, SkillStatus
from core.skill_registry import SkillRegistry


class TestSkillRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SkillRegistry()
        self.skill1 = Skill(
            skill_id="SKL-0001",
            name="Deploy DB",
            description="Deploys database clusters",
            owner_id="EXEC-0002",
            department="Operations",
            execution_engine="Antigravity",
            capabilities=["db", "postgres"],
            inputs=["spec"],
            outputs=["host"],
            version="1.0",
        )
        self.skill2 = Skill(
            skill_id="SKL-0002",
            name="Compile Code",
            description="Compiles source code",
            owner_id="EXEC-0003",
            department="Engineering",
            execution_engine="Vite",
            capabilities=["compiler", "build"],
            inputs=["src"],
            outputs=["dist"],
            version="2.0",
            status=SkillStatus.BUSY,
        )

    def test_register_and_unregister(self) -> None:
        self.registry.register(self.skill1)
        self.assertEqual(len(self.registry.list_skills()), 1)
        self.assertEqual(self.registry.find_by_id("SKL-0001"), self.skill1)

        # Re-registering raises duplicate error
        with self.assertRaises(ValueError):
            self.registry.register(self.skill1)

        # Unregistering
        unreg = self.registry.unregister("SKL-0001")
        self.assertEqual(unreg, self.skill1)
        self.assertEqual(len(self.registry.list_skills()), 0)

        # Unregistering non-existent raises error
        with self.assertRaises(ValueError):
            self.registry.unregister("SKL-9999")

    def test_find_by_capability(self) -> None:
        self.registry.register(self.skill1)
        self.registry.register(self.skill2)

        matches_db = self.registry.find_by_capability("db")
        self.assertEqual(matches_db, [self.skill1])

        matches_compiler = self.registry.find_by_capability("compiler")
        self.assertEqual(matches_compiler, [self.skill2])

        matches_none = self.registry.find_by_capability("rust")
        self.assertEqual(matches_none, [])

        with self.assertRaises(ValueError):
            self.registry.find_by_capability("")

    def test_find_by_owner(self) -> None:
        self.registry.register(self.skill1)
        self.registry.register(self.skill2)

        matches_exec2 = self.registry.find_by_owner("EXEC-0002")
        self.assertEqual(matches_exec2, [self.skill1])

        matches_exec3 = self.registry.find_by_owner("EXEC-0003")
        self.assertEqual(matches_exec3, [self.skill2])

        with self.assertRaises(ValueError):
            self.registry.find_by_owner("")

    def test_list_available(self) -> None:
        self.registry.register(self.skill1)  # AVAILABLE by default
        self.registry.register(self.skill2)  # BUSY
        
        available = self.registry.list_available()
        self.assertEqual(available, [self.skill1])

    def test_summary_and_serialization(self) -> None:
        self.registry.register(self.skill1)
        self.registry.register(self.skill2)

        summary = self.registry.summary()
        self.assertEqual(summary["total_registered_skills"], 2)
        self.assertEqual(summary["skills_by_status"], {"AVAILABLE": 1, "BUSY": 1})
        self.assertEqual(summary["skills_by_department"], {"Operations": 1, "Engineering": 1})

        to_dict_out = self.registry.to_dict()
        self.assertEqual(len(to_dict_out["skills"]), 2)
        self.assertEqual(to_dict_out["summary"], summary)
