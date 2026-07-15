Specification 048 — Client Portal & Collaboration Workspace
Goal Description

Implement the Client Portal — a secure, branded workspace where clients collaborate with JBK Technologies throughout the entire engagement lifecycle.

The portal provides visibility into projects, proposals, deliverables, invoices, communications, milestones, approvals, and support while maintaining strict separation between client-facing information and internal JBK operational data.

The Client Portal is presentation-only and consumes existing JBK OS engines.

Architectural Principles

The Client Portal:

Contains no business logic
Consumes existing engines
Never exposes confidential internal data
Uses role-based access
Maintains immutable audit history
Supports document collaboration
Supports real-time updates
Operates independently for every client workspace
Proposed Changes
1. Client Workspace
NEW
portal/
    app.py
    routes.py
    workspace_controller.py
    websocket_manager.py

Responsibilities

Portal routing
Client authentication hooks
Workspace loading
Live updates
File access
Notifications

No business logic.

2. Client Workspace Models
NEW
core/client_workspace.py

Contains

ClientWorkspace

WorkspaceSection

WorkspaceNotification

WorkspaceActivity

WorkspaceSummary

WorkspacePermission
3. Client Portal Controller
NEW
core/client_portal_controller.py

Loads information from

CRM Engine

Proposal Generator

Project Initialization

Delivery Supervision

Financial Operations

Client Success

Communication Engine

Client Delivery & Handover

Methods

load_workspace()

load_projects()

load_proposals()

load_deliverables()

load_documents()

load_messages()

load_invoices()

load_support()

load_activity()

approve_proposal()

approve_milestone()

submit_feedback()
4. Workspace Dashboard

Client sees

Welcome
Welcome back,

Acme Schools
Current Projects

Status

Progress

Milestones

Estimated completion

Proposal

Proposal history

Pending approvals

Accepted proposals

Deliverables

Completed deliverables

Downloads

Version history

Acceptance status

Documents

Contracts

Requirements

Meeting notes

Training manuals

Architecture

Invoices

Receipts

Communication Center

Conversation with JBK

Announcements

Questions

Meeting invitations

Notifications

Financial

Invoices

Payments

Outstanding balances

Payment history

Upcoming invoices

Support

Support tickets

Knowledge articles

Scheduled reviews

Warranty status

Customer Success plan

Activity Feed

Example

Proposal Approved

Project Started

Architecture Completed

Milestone Accepted

Invoice Issued

Payment Received

Support Ticket Closed

Training Completed
5. Client Approvals

Clients can approve

Proposal

Milestone

Deliverable

Change Request

Acceptance

Every approval creates an immutable audit record.

6. Secure File Repository

Supports

Upload

Download

Version history

Comments

Preview

Files include

PDF

DOCX

Images

Videos

Architecture diagrams

Training materials

7. Notifications

Examples

New Deliverable Ready

Invoice Available

Meeting Scheduled

Milestone Awaiting Approval

Project Updated

Support Response Received

Uses Communication Engine.

8. Real-Time Collaboration

WebSocket updates

Project progress

Messages

Deliverables

Notifications

Support

Activity feed

9. Client Feedback

Client can submit

Satisfaction

Comments

Feature requests

Issues

Automatically routes into

CRM

Client Success

Knowledge Registry

Continuous Improvement

10. Security

Every workspace isolated.

Client A can never access Client B.

Internal notes hidden.

Pricing calculations hidden.

Executive discussions hidden.

Strategic reports hidden.

Knowledge Registry hidden.

Business Rules
BR-048-001

Client Portal is presentation-only.

BR-048-002

Internal planning information is never exposed.

BR-048-003

Every approval is auditable.

BR-048-004

Every document has version history.

BR-048-005

Portal displays live project status.

BR-048-006

Client cannot modify internal work orders.

BR-048-007

Support requests automatically create CRM interactions.

BR-048-008

Feedback automatically feeds Continuous Improvement.

BR-048-009

Portal gracefully degrades when subsystems unavailable.

BR-048-010

All portal data is serializable.

Tests
NEW
tests/test_client_portal.py

Approximately 35–40 tests

Covering

Workspace loading
Client isolation
Proposal approval
Deliverable downloads
Notifications
Activity feed
Document versioning
Support requests
Feedback routing
Serialization
Permission boundaries
Missing subsystem handling
Brain Entry
Client-Portal-Standards.md

Contents

# Client Portal Standards

1. Client Portal is presentation-only.

2. Client workspaces are fully isolated.

3. Internal company information is never exposed.

4. Every approval is auditable.

5. Every client interaction contributes to CRM history.

6. Documents maintain immutable version history.

7. Portal remains operational even when individual subsystems are unavailable.
Verification Plan
Automated
python -m unittest discover -s tests

Expected

All tests pass
Manual
Launch Client Portal.
Authenticate as a sample client.
Verify workspace loads.
Review active project.
Download a deliverable.
Approve a milestone.
View invoice.
Send a support request.
Confirm activity feed updates.
Verify internal JBK-only information is not visible.