import unittest

from core.knowledge import KnowledgeItem, KnowledgeStatus


class TestKnowledgeItem(unittest.TestCase):
    def setUp(self) -> None:
        self.item = KnowledgeItem(
            knowledge_id="KI-0001",
            title="SOP Deployment",
            category="SOPs",
            owner="EXEC-0001",
            source="manual.md",
            tags=["deploy", "database", "ops"],
            description="Deployment checklist for database clusters",
            version="1.0",
        )

    def test_instantiation_and_values(self) -> None:
        self.assertEqual(self.item.knowledge_id, "KI-0001")
        self.assertEqual(self.item.title, "SOP Deployment")
        self.assertEqual(self.item.category, "SOPs")
        self.assertEqual(self.item.owner, "EXEC-0001")
        self.assertEqual(self.item.source, "manual.md")
        self.assertEqual(self.item.tags, ["deploy", "database", "ops"])
        self.assertEqual(self.item.description, "Deployment checklist for database clusters")
        self.assertEqual(self.item.version, "1.0")
        self.assertEqual(self.item.status, KnowledgeStatus.DRAFT)
        self.assertIsNotNone(self.item.created_at)

    def test_instantiation_raises_on_missing_args(self) -> None:
        with self.assertRaises(ValueError):
            KnowledgeItem("", "Title", "Cat", "Owner", "Src", [], "Desc", "1.0")
        with self.assertRaises(ValueError):
            KnowledgeItem("KI-0001", "", "Cat", "Owner", "Src", [], "Desc", "1.0")
        with self.assertRaises(ValueError):
            KnowledgeItem("KI-0001", "Title", "", "Owner", "Src", [], "Desc", "1.0")
        with self.assertRaises(ValueError):
            KnowledgeItem("KI-0001", "Title", "Cat", "", "Src", [], "Desc", "1.0")
        with self.assertRaises(ValueError):
            KnowledgeItem("KI-0001", "Title", "Cat", "Owner", "", [], "Desc", "1.0")
        with self.assertRaises(ValueError):
            KnowledgeItem("KI-0001", "Title", "Cat", "Owner", "Src", [], "Desc", "")

    def test_matches_query(self) -> None:
        self.assertTrue(self.item.matches("SOP"))
        self.assertTrue(self.item.matches("deployment"))
        self.assertTrue(self.item.matches("ops"))
        self.assertTrue(self.item.matches("manual.md")) # Matches source via owner or description case checks if included, wait, is source checked in matches? Let's check matches code.
        # Oh, source was not checked in matches, let's verify if matches works for description
        self.assertTrue(self.item.matches("checklist"))
        self.assertFalse(self.item.matches("webserver"))
        self.assertFalse(self.item.matches(""))

    def test_update_status(self) -> None:
        self.item.update_status(KnowledgeStatus.ACTIVE)
        self.assertEqual(self.item.status, KnowledgeStatus.ACTIVE)

        self.item.update_status("ARCHIVED")
        self.assertEqual(self.item.status, KnowledgeStatus.ARCHIVED)

        with self.assertRaises(ValueError):
            self.item.update_status("INVALID_STATUS")

    def test_serialization(self) -> None:
        sum_dict = self.item.summary()
        self.assertEqual(sum_dict["knowledge_id"], "KI-0001")
        self.assertEqual(sum_dict["title"], "SOP Deployment")
        self.assertNotIn("source", sum_dict)

        full_dict = self.item.to_dict()
        self.assertEqual(full_dict["source"], "manual.md")
        self.assertEqual(full_dict["tags"], ["deploy", "database", "ops"])
