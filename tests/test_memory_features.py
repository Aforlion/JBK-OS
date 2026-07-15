import unittest
from datetime import datetime, timezone
from core.memory_record import MemoryRecord
from core.memory_registry import MemoryRegistry
from core.organizational_memory_engine import OrganizationalMemoryEngine


class TestMemoryFeatures(unittest.TestCase):

    def test_memory_record_creation_and_matching(self) -> None:
        rec = MemoryRecord(
            memory_id="MEM-0001",
            category="meeting",
            title="SaaS Architecture Kickoff",
            summary="Kickoff with Ministry of Education",
            full_context="Detailed discussion regarding database design and GDPR security compliance.",
            related_entities=["PROJ-0001", "Client-MOE"],
            created_by="system",
            confidence=0.95,
            importance=8,
            tags=["architecture", "SaaS", "GDPR"],
            source_engine="DiscoveryConversationEngine",
        )

        self.assertEqual(rec.id, "MEM-0001")
        self.assertEqual(rec.category, "meeting")
        self.assertFalse(rec.archived)

        # Matching checks
        self.assertTrue(rec.matches("architecture"))
        self.assertTrue(rec.matches("GDPR"))
        self.assertTrue(rec.matches("Client-MOE"))
        self.assertFalse(rec.matches("random-query-no-match"))

        # dict checks
        d = rec.to_dict()
        self.assertEqual(d["id"], "MEM-0001")
        self.assertEqual(d["confidence"], 0.95)

    def test_memory_registry_operations(self) -> None:
        reg = MemoryRegistry()

        rec1 = MemoryRecord(
            memory_id="MEM-0001",
            category="meeting",
            title="School Automation",
            summary="First sync",
            full_context="Notes on requirements",
            related_entities=["PROJ-0001", "Client-MOE"],
            tags=["school", "sync"],
        )

        reg.register(rec1)
        self.assertEqual(len(reg.list_items()), 1)

        # Merging duplicate memory test
        rec2 = MemoryRecord(
            memory_id="MEM-0002",
            category="meeting",
            title="School Automation",
            summary="Second sync",
            full_context="Different context details",
            related_entities=["PROJ-0001", "EXEC-0002"],
            tags=["school", "different-tag"],
            importance=9,
            confidence=0.8,
        )

        merged = reg.register(rec2)
        # Length remains 1 because they merged
        self.assertEqual(len(reg.list_items()), 1)
        self.assertEqual(merged.id, "MEM-0001")
        self.assertIn("Different context details", merged.full_context)
        self.assertEqual(merged.importance, 9)
        self.assertIn("different-tag", merged.tags)
        self.assertIn("EXEC-0002", merged.related_entities)

        # Search checks
        self.assertEqual(len(reg.search("school")), 1)
        self.assertEqual(len(reg.search("nonexistent")), 0)

        # client/project/tag retrieval
        self.assertEqual(len(reg.find_by_client("Client-MOE")), 1)
        self.assertEqual(len(reg.find_by_project("PROJ-0001")), 1)
        self.assertEqual(len(reg.find_by_tag("different-tag")), 1)

        # Archival check
        reg.archive("MEM-0001")
        self.assertTrue(reg.list_items()[0].archived)
        # Search doesn't return archived
        self.assertEqual(len(reg.search("school")), 0)

    def test_memory_engine_remember_and_recall(self) -> None:
        engine = OrganizationalMemoryEngine()

        # Capture memories
        engine.remember(
            category="client",
            title="Client Budget Negotiation",
            summary="Client prefers lower initial license cost.",
            full_context="Ministry of Education prefers paying for annual support rather than heavy upfront license fee.",
            related_entities=["Client-MOE"],
            importance=9,
            confidence=0.9,
            tags=["budget", "licensing"],
        )

        engine.remember(
            category="meeting",
            title="School Automation Setup",
            summary="Setup server environment.",
            full_context="Encountered firewall issues on local server deployment.",
            related_entities=["PROJ-0002"],
            importance=6,
            confidence=0.95,
            tags=["server", "deployment"],
        )

        # Query recall
        results = engine.recall("MOE")
        self.assertGreater(len(results), 0)

        best_match = results[0]
        self.assertEqual(best_match["record"].title, "Client Budget Negotiation")
        self.assertIn("✓ Match found in related entities", best_match["explanation"])
        self.assertEqual(best_match["confidence_pct"], 90)

        # Query by category
        results_meeting = engine.recall("", category="meeting")
        self.assertEqual(len(results_meeting), 1)
        self.assertEqual(results_meeting[0]["record"].title, "School Automation Setup")


if __name__ == "__main__":
    unittest.main()
