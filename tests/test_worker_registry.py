import unittest

from core.executive import Executive, ExecutiveStatus
from core.worker_registry import WorkerRegistry


class WorkerRegistryTest(unittest.TestCase):
    def test_worker_registry_can_be_instantiated(self):
        registry = WorkerRegistry()

        self.assertEqual(registry.list_workers(), [])

    def test_workers_can_be_registered(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0001",
            title="Chief Technology Officer",
            mission="Own technology outcomes.",
        )

        registered_worker = registry.register(worker)

        self.assertIs(registered_worker, worker)
        self.assertEqual(registry.list_workers(), [worker])

    def test_duplicate_worker_ids_are_rejected(self):
        registry = WorkerRegistry()
        first_worker = Executive(
            executive_id="EXEC-0002",
            title="Chief Product Officer",
            mission="Own product outcomes.",
        )
        second_worker = Executive(
            executive_id="EXEC-0002",
            title="Chief Research Officer",
            mission="Own research outcomes.",
        )
        registry.register(first_worker)

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register(second_worker)

    def test_workers_can_be_removed(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0003",
            title="Chief Finance Officer",
            mission="Own finance outcomes.",
        )
        registry.register(worker)

        removed_worker = registry.unregister("EXEC-0003")

        self.assertIs(removed_worker, worker)
        self.assertEqual(registry.list_workers(), [])
        self.assertIsNone(registry.find_by_id("EXEC-0003"))

    def test_unregister_removes_only_registry_reference(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0004",
            title="Chief Operating Officer",
            mission="Own operating outcomes.",
        )
        registry.register(worker)

        removed_worker = registry.unregister("EXEC-0004")

        self.assertIs(removed_worker, worker)
        self.assertEqual(worker.id, "EXEC-0004")
        self.assertEqual(worker.title, "Chief Operating Officer")

    def test_workers_can_be_found_by_id(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0005",
            title="Chief Customer Officer",
            mission="Own customer outcomes.",
        )
        registry.register(worker)

        found_worker = registry.find_by_id("EXEC-0005")

        self.assertIs(found_worker, worker)

    def test_workers_can_be_found_by_role(self):
        registry = WorkerRegistry()
        first_worker = Executive(
            executive_id="EXEC-0006",
            title="Chief Research Officer",
            mission="Own research outcomes.",
        )
        second_worker = Executive(
            executive_id="EXEC-0007",
            title="Chief Research Officer",
            mission="Own research operations.",
        )
        third_worker = Executive(
            executive_id="EXEC-0008",
            title="Chief Legal Officer",
            mission="Own legal outcomes.",
        )
        registry.register(first_worker)
        registry.register(second_worker)
        registry.register(third_worker)

        found_workers = registry.find_by_role("Chief Research Officer")

        self.assertEqual(found_workers, [first_worker, second_worker])

    def test_available_workers_can_be_listed(self):
        registry = WorkerRegistry()
        available_worker = Executive(
            executive_id="EXEC-0009",
            title="Chief Marketing Officer",
            mission="Own marketing outcomes.",
            status=ExecutiveStatus.AVAILABLE,
        )
        busy_worker = Executive(
            executive_id="EXEC-0010",
            title="Chief People Officer",
            mission="Own people outcomes.",
            status=ExecutiveStatus.BUSY,
        )
        registry.register(available_worker)
        registry.register(busy_worker)

        available_workers = registry.list_available()

        self.assertEqual(available_workers, [available_worker])

    def test_registry_does_not_change_worker_state(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0011",
            title="Chief AI Officer",
            mission="Own AI outcomes.",
            status=ExecutiveStatus.OFFLINE,
        )

        registry.register(worker)
        registry.unregister("EXEC-0011")

        self.assertEqual(worker.status, ExecutiveStatus.OFFLINE)

    def test_summary_returns_structured_information(self):
        registry = WorkerRegistry()
        available_worker = Executive(
            executive_id="EXEC-0012",
            title="Chief of Staff",
            mission="Coordinate executive work.",
            status=ExecutiveStatus.AVAILABLE,
        )
        busy_worker = Executive(
            executive_id="EXEC-0013",
            title="Chief of Staff",
            mission="Coordinate strategic execution.",
            status=ExecutiveStatus.BUSY,
        )
        offline_worker = Executive(
            executive_id="EXEC-0014",
            title="Chief Technology Officer",
            mission="Own technology outcomes.",
            status=ExecutiveStatus.OFFLINE,
        )
        suspended_worker = Executive(
            executive_id="EXEC-0015",
            title="Chief Legal Officer",
            mission="Own legal outcomes.",
            status=ExecutiveStatus.SUSPENDED,
        )
        registry.register(available_worker)
        registry.register(busy_worker)
        registry.register(offline_worker)
        registry.register(suspended_worker)

        summary = registry.summary()

        self.assertEqual(
            summary,
            {
                "total_registered_workers": 4,
                "workers_by_role": {
                    "Chief of Staff": 2,
                    "Chief Technology Officer": 1,
                    "Chief Legal Officer": 1,
                },
                "available_workers": 1,
                "busy_workers": 1,
                "offline_workers": 1,
                "suspended_workers": 1,
            },
        )

    def test_to_dict_returns_serializable_representation(self):
        registry = WorkerRegistry()
        worker = Executive(
            executive_id="EXEC-0016",
            title="Chief Revenue Officer",
            mission="Own revenue outcomes.",
        )
        registry.register(worker)

        registry_dict = registry.to_dict()

        self.assertEqual(registry_dict["workers"], [worker.to_dict()])
        self.assertEqual(registry_dict["summary"]["total_registered_workers"], 1)

    def test_register_requires_worker_id(self):
        registry = WorkerRegistry()

        with self.assertRaisesRegex(ValueError, "Worker must have an ID"):
            registry.register(object())


if __name__ == "__main__":
    unittest.main()
