import unittest
from datetime import datetime, timezone
from core.execution_engine import ExecutionStatus, ExecutionResult
from core.antigravity_execution_engine import AntigravityExecutionEngine
from core.work_order import WorkOrder


class TestExecutionEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = AntigravityExecutionEngine()
        self.work_order = WorkOrder(
            project_id="PROJ-0001",
            title="Setup DB",
            objective="Install postgres",
            work_order_id="WO-0001",
        )

    def test_execution_result_serialization(self) -> None:
        started = datetime.now(timezone.utc).isoformat()
        completed = datetime.now(timezone.utc).isoformat()
        result = ExecutionResult(
            execution_id="EXE-0001",
            work_order_id="WO-0001",
            status=ExecutionStatus.COMPLETED,
            started_at=started,
            completed_at=completed,
            output="Done",
            metadata={"test": True},
        )

        sum_dict = result.summary()
        self.assertEqual(sum_dict["execution_id"], "EXE-0001")
        self.assertEqual(sum_dict["work_order_id"], "WO-0001")
        self.assertEqual(sum_dict["status"], "COMPLETED")
        self.assertEqual(sum_dict["started_at"], started)
        self.assertEqual(sum_dict["completed_at"], completed)
        self.assertNotIn("output", sum_dict)

        full_dict = result.to_dict()
        self.assertEqual(full_dict["output"], "Done")
        self.assertEqual(full_dict["metadata"], {"test": True})

    def test_execution_result_raises_on_invalid_args(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionResult("", "WO-0001", ExecutionStatus.PENDING)
        with self.assertRaises(ValueError):
            ExecutionResult("EXE-0001", "", ExecutionStatus.PENDING)
        with self.assertRaises(ValueError):
            ExecutionResult("EXE-0001", "WO-0001", None)

    def test_supports_method(self) -> None:
        self.assertTrue(self.engine.supports("antigravity"))
        self.assertTrue(self.engine.supports("mock"))
        self.assertTrue(self.engine.supports("python"))
        self.assertFalse(self.engine.supports("rust"))
        self.assertFalse(self.engine.supports(""))

    def test_successful_execution(self) -> None:
        initial_status = self.work_order.status
        
        result = self.engine.execute(self.work_order)
        
        # Verify the WorkOrder itself was not mutated directly by the engine
        self.assertEqual(self.work_order.status, initial_status)
        
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.work_order_id, "WO-0001")
        self.assertIn("Simulated successful execution", result.output)
        self.assertEqual(self.engine.status(result.execution_id), ExecutionStatus.COMPLETED)

    def test_failed_execution(self) -> None:
        self.engine.fail_next = True
        result = self.engine.execute(self.work_order)
        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertIn("Simulated execution failure", result.output)
        self.assertEqual(self.engine.status(result.execution_id), ExecutionStatus.FAILED)

    def test_failed_execution_by_title(self) -> None:
        wo_fail = WorkOrder(
            project_id="PROJ-0001",
            title="Database Fail Task",
            objective="Fail intentionally",
            work_order_id="WO-0002",
        )
        result = self.engine.execute(wo_fail)
        self.assertEqual(result.status, ExecutionStatus.FAILED)

    def test_result_retrieval(self) -> None:
        result = self.engine.execute(self.work_order)
        retrieved = self.engine.result(result.execution_id)
        self.assertIs(result, retrieved)

        # Non-existent ID returns None
        self.assertIsNone(self.engine.result("EXE-9999"))

    def test_cancellation_unsupported_for_completed(self) -> None:
        result = self.engine.execute(self.work_order)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        
        # Since it completed immediately, cancel should return False
        cancelled = self.engine.cancel(result.execution_id)
        self.assertFalse(cancelled)
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_cancellation_for_pending_running(self) -> None:
        # Manually create a running execution in engine storage
        exec_id = "EXE-0999"
        result = ExecutionResult(
            execution_id=exec_id,
            work_order_id="WO-0001",
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        self.engine.executions[exec_id] = result
        
        cancelled = self.engine.cancel(exec_id)
        self.assertTrue(cancelled)
        self.assertEqual(result.status, ExecutionStatus.CANCELLED)
        self.assertIsNotNone(result.completed_at)

    def test_execution_methods_raise_on_empty_args(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.execute(None)
        with self.assertRaises(ValueError):
            wo_no_id = WorkOrder(
                project_id="PROJ-0001",
                title="No ID",
                objective="No ID objective",
            )
            # Remove ID manually
            wo_no_id._id = ""
            self.engine.execute(wo_no_id)

        with self.assertRaises(ValueError):
            self.engine.status("")
        with self.assertRaises(ValueError):
            self.engine.cancel("")
        with self.assertRaises(ValueError):
            self.engine.result("")
            
        with self.assertRaises(ValueError):
            self.engine.status("EXE-9999")
