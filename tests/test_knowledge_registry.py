import unittest

from core.knowledge import KnowledgeItem, KnowledgeStatus
from core.knowledge_registry import KnowledgeRegistry


class TestKnowledgeRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = KnowledgeRegistry()
        self.item1 = KnowledgeItem(
            knowledge_id="KI-0001",
            title="SOP Deployment",
            category="SOPs",
            owner="EXEC-0001",
            source="manual.md",
            tags=["deploy", "database"],
            description="Deployment checklist for database clusters",
            version="1.0",
        )
        self.item2 = KnowledgeItem(
            knowledge_id="KI-0002",
            title="Architecture Specs",
            category="Architecture",
            owner="EXEC-0002",
            source="arch.md",
            tags=["infrastructure", "ops"],
            description="System topology and layout specs",
            version="2.0",
            status=KnowledgeStatus.ARCHIVED,
        )

    def test_register_and_unregister(self) -> None:
        self.registry.register(self.item1)
        self.assertEqual(len(self.registry.list_items()), 1)
        self.assertEqual(self.registry.find_by_id("KI-0001"), self.item1)

        # Duplicate ID rejection
        with self.assertRaises(ValueError):
            self.registry.register(self.item1)

        # Unregistering
        unreg = self.registry.unregister("KI-0001")
        self.assertEqual(unreg, self.item1)
        self.assertEqual(len(self.registry.list_items()), 0)

        # Unregistering missing raises error
        with self.assertRaises(ValueError):
            self.registry.unregister("KI-9999")

    def test_find_by_category(self) -> None:
        self.registry.register(self.item1)
        self.registry.register(self.item2)

        matches_sops = self.registry.find_by_category("SOPs")
        self.assertEqual(matches_sops, [self.item1])

        with self.assertRaises(ValueError):
            self.registry.find_by_category("")

    def test_find_by_owner(self) -> None:
        self.registry.register(self.item1)
        self.registry.register(self.item2)

        matches_exec1 = self.registry.find_by_owner("EXEC-0001")
        self.assertEqual(matches_exec1, [self.item1])

        with self.assertRaises(ValueError):
            self.registry.find_by_owner("")

    def test_find_by_tag(self) -> None:
        self.registry.register(self.item1)
        self.registry.register(self.item2)

        matches_deploy = self.registry.find_by_tag("deploy")
        self.assertEqual(matches_deploy, [self.item1])

        matches_ops = self.registry.find_by_tag("ops")
        self.assertEqual(matches_ops, [self.item2])

        with self.assertRaises(ValueError):
            self.registry.find_by_tag("")

    def test_search_and_discoverability(self) -> None:
        self.registry.register(self.item1)
        self.registry.register(self.item2) # Archived

        # Search matches both on keywords
        res = self.registry.search("deploy")
        self.assertEqual(res, [self.item1])

        # BR-0027: Archived knowledge remains discoverable
        res_archived = self.registry.search("specs")
        self.assertEqual(res_archived, [self.item2])

        # Empty search query returns all registered items
        self.assertEqual(len(self.registry.search("")), 2)

    def test_summary_and_serialization(self) -> None:
        self.registry.register(self.item1)
        self.registry.register(self.item2)

        summary = self.registry.summary()
        self.assertEqual(summary["total_registered_items"], 2)
        self.assertEqual(summary["items_by_status"], {"DRAFT": 1, "ARCHIVED": 1})
        self.assertEqual(summary["items_by_category"], {"SOPs": 1, "Architecture": 1})

        to_dict_out = self.registry.to_dict()
        self.assertEqual(len(to_dict_out["items"]), 2)
        self.assertEqual(to_dict_out["summary"], summary)
