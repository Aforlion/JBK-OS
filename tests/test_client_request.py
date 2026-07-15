import unittest

from core.client_request import (
    ClientRequest,
    ClientRequestPriority,
    ClientRequestStatus,
)


class ClientRequestTest(unittest.TestCase):
    def test_client_request_can_be_instantiated(self):
        request = self._create_request(request_id="CR-0001")

        self.assertEqual(request.id, "CR-0001")
        self.assertEqual(request.client_name, "Avery Jordan")
        self.assertEqual(request.organization, "Example Organization")
        self.assertEqual(request.contact_person, "Avery Jordan")
        self.assertEqual(request.contact_email, "avery@example.com")
        self.assertEqual(request.contact_phone, "+1-555-0100")
        self.assertEqual(request.industry, "Education")
        self.assertEqual(request.title, "Workflow Assessment")
        self.assertEqual(request.problem_statement, "The client needs clearer workflows.")
        self.assertEqual(request.desired_outcome, "A documented operating workflow.")
        self.assertEqual(request.priority, ClientRequestPriority.MEDIUM)
        self.assertEqual(request.status, ClientRequestStatus.NEW)
        self.assertTrue(request.created_at)
        self.assertTrue(request.updated_at)
        self.assertIsNone(request.approved_at)
        self.assertIsNone(request.project_id)
        self.assertEqual(request.notes, [])

    def test_immutable_ids_are_generated(self):
        request = self._create_request()

        self.assertRegex(request.id, r"^CR-\d{4}$")

    def test_id_is_immutable(self):
        request = self._create_request(request_id="CR-0002")

        with self.assertRaises(AttributeError):
            request.id = "CR-9999"

    def test_status_transitions_function_correctly(self):
        approved_request = self._create_request(request_id="CR-0003")
        rejected_request = self._create_request(request_id="CR-0004")
        withdrawn_request = self._create_request(request_id="CR-0005")

        self.assertEqual(approved_request.approve(), ClientRequestStatus.APPROVED)
        self.assertEqual(approved_request.status, ClientRequestStatus.APPROVED)
        self.assertTrue(approved_request.approved_at)

        self.assertEqual(rejected_request.reject(), ClientRequestStatus.REJECTED)
        self.assertEqual(rejected_request.status, ClientRequestStatus.REJECTED)

        self.assertEqual(withdrawn_request.withdraw(), ClientRequestStatus.WITHDRAWN)
        self.assertEqual(withdrawn_request.status, ClientRequestStatus.WITHDRAWN)

    def test_priority_updates_correctly(self):
        request = self._create_request(request_id="CR-0006")
        original_updated_at = request.updated_at

        priority = request.update_priority("CRITICAL")

        self.assertEqual(priority, ClientRequestPriority.CRITICAL)
        self.assertEqual(request.priority, ClientRequestPriority.CRITICAL)
        self.assertNotEqual(request.updated_at, original_updated_at)

    def test_project_linking_is_restricted_to_approved_requests(self):
        request = self._create_request(request_id="CR-0007")

        with self.assertRaisesRegex(ValueError, "Only APPROVED"):
            request.link_project("PROJ-0001")

        request.approve()
        project_id = request.link_project("PROJ-0001")

        self.assertEqual(project_id, "PROJ-0001")
        self.assertEqual(request.project_id, "PROJ-0001")
        self.assertEqual(request.status, ClientRequestStatus.PROJECT_CREATED)

    def test_client_request_can_be_linked_to_only_one_project(self):
        request = self._create_request(request_id="CR-0008")
        request.approve()
        request.link_project("PROJ-0001")

        with self.assertRaisesRegex(ValueError, "only one Project"):
            request.link_project("PROJ-0002")

    def test_notes_are_stored_chronologically(self):
        request = self._create_request(request_id="CR-0009")

        first_note = request.add_note("Initial discovery call completed.")
        second_note = request.add_note("Client sent additional context.")

        self.assertEqual(request.notes, [first_note, second_note])
        self.assertEqual(request.notes[0]["note"], "Initial discovery call completed.")
        self.assertEqual(request.notes[1]["note"], "Client sent additional context.")

    def test_rejected_and_withdrawn_requests_are_read_only_except_for_notes(self):
        rejected_request = self._create_request(request_id="CR-0010")
        withdrawn_request = self._create_request(request_id="CR-0011")
        rejected_request.reject()
        withdrawn_request.withdraw()

        with self.assertRaisesRegex(ValueError, "read-only"):
            rejected_request.update_priority(ClientRequestPriority.HIGH)
        with self.assertRaisesRegex(ValueError, "read-only"):
            withdrawn_request.approve()

        note = rejected_request.add_note("Client may return next quarter.")

        self.assertEqual(rejected_request.notes, [note])

    def test_summary_returns_structured_information(self):
        request = self._create_request(
            request_id="CR-0012",
            priority=ClientRequestPriority.HIGH,
        )
        request.approve()
        request.link_project("PROJ-0012")

        summary = request.summary()

        self.assertEqual(
            summary,
            {
                "id": "CR-0012",
                "client_name": "Avery Jordan",
                "organization": "Example Organization",
                "title": "Workflow Assessment",
                "status": "PROJECT_CREATED",
                "priority": "HIGH",
                "industry": "Education",
                "project_id": "PROJ-0012",
                "created_at": request.created_at,
                "updated_at": request.updated_at,
            },
        )

    def test_to_dict_returns_serializable_representation(self):
        request = self._create_request(request_id="CR-0013")
        note = request.add_note("Client asked for a phased approach.")

        request_dict = request.to_dict()

        self.assertEqual(
            request_dict,
            {
                "id": "CR-0013",
                "client_name": "Avery Jordan",
                "organization": "Example Organization",
                "contact_person": "Avery Jordan",
                "contact_email": "avery@example.com",
                "contact_phone": "+1-555-0100",
                "industry": "Education",
                "title": "Workflow Assessment",
                "problem_statement": "The client needs clearer workflows.",
                "desired_outcome": "A documented operating workflow.",
                "priority": "MEDIUM",
                "status": "NEW",
                "created_at": request.created_at,
                "updated_at": request.updated_at,
                "approved_at": None,
                "project_id": None,
                "notes": [note],
            },
        )

    def test_required_fields_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "Client name is required"):
            self._create_request(client_name="")

    def test_invalid_priority_fails_clearly(self):
        with self.assertRaisesRegex(ValueError, "Invalid client request priority"):
            self._create_request(priority="URGENT")

    def _create_request(
        self,
        request_id=None,
        client_name="Avery Jordan",
        organization="Example Organization",
        contact_person="Avery Jordan",
        contact_email="avery@example.com",
        contact_phone="+1-555-0100",
        industry="Education",
        title="Workflow Assessment",
        problem_statement="The client needs clearer workflows.",
        desired_outcome="A documented operating workflow.",
        priority=ClientRequestPriority.MEDIUM,
    ):
        return ClientRequest(
            request_id=request_id,
            client_name=client_name,
            organization=organization,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone,
            industry=industry,
            title=title,
            problem_statement=problem_statement,
            desired_outcome=desired_outcome,
            priority=priority,
        )


if __name__ == "__main__":
    unittest.main()
