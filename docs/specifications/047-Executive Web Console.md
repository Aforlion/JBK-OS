Specification 047 — Executive Web Console & Operational Command Center
Goal Description

Build the Executive Web Console — the primary graphical interface for JBK OS. The console enables executives to operate the company through a secure browser-based dashboard, providing live visibility into operations, natural-language interaction with the AI Executive Assistant, executive approvals, project monitoring, and organizational health.

This specification introduces the presentation layer only. It must consume existing JBK OS engines and models without embedding business logic.

Architectural Principles

The Executive Web Console shall:

Contain no business logic
Consume existing JBK OS engines
Be fully stateless
Refresh from live engine outputs
Support desktop and tablet layouts
Gracefully degrade when subsystems are unavailable
Never bypass decision boundaries enforced by the backend
Proposed Changes
1. Web Application Layer
NEW
web/
    app.py
    routes.py
    dashboard_api.py
    websocket_manager.py

Purpose:

Host the Executive Console.

Responsibilities:

HTTP endpoints
Session routing
Dashboard API
WebSocket events
Authentication hooks (placeholder for Spec 051)

No business logic.

2. Dashboard View Models
NEW
core/dashboard_view_model.py

Models optimized for UI rendering.

DashboardViewModel

ExecutiveCard

ProjectCard

AlertCard

KPIWidget

ConversationWidget

ActivityFeedItem

QuickAction

NavigationSection

These convert existing engine outputs into presentation objects.

3. Executive Console Controller
NEW
core/executive_console_controller.py

Responsibilities

Loads:

ExecutiveDashboardEngine

PortfolioEngine

CRMEngine

DeliverySupervisionEngine

AIExecutiveAssistant

StrategicIntelligenceEngine

ExecutiveMeetingEngine

Returns:

ExecutiveDashboardView

Methods

load_dashboard()

refresh_dashboard()

load_projects()

load_alerts()

load_portfolio()

load_strategy()

load_activity_feed()

load_conversations()

load_meetings()

search()

quick_action()
4. Natural Language Command Bar

Top-center command bar.

Example:

> We have a new client

> Review Acme project

> Show company health

> Any opportunities in healthcare?

> Prepare proposal

> Schedule executive meeting

Internally routes directly into

AIExecutiveAssistant.converse()

No duplicated orchestration.

5. Live Dashboard Widgets

Dashboard sections:

Company Health

Overall Health

Revenue

Projects

Clients

Delivery

Knowledge

Strategic Readiness

Executive Alerts

Critical

Warning

Information

Pulled from

ExecutiveDashboardEngine

Active Projects

Project cards

Progress

Risk

Owner

Status

Completion %

Executive Briefing

Today's priorities

Open approvals

CEO attention items

Generated from

AIExecutiveAssistant.generate_startup_briefing()

Portfolio

Clients

Revenue

Renewals

Delivery Success

Pipeline

AI Assistant Panel

Persistent conversation

Conversation history

Suggested actions

Execution timeline

Knowledge Feed

Recently learned lessons

Recently promoted standards

Organizational improvements

Meetings

Upcoming executive meetings

Action items

6. Activity Feed

Every important company event appears here.

Examples

Proposal approved

New client onboarded

Project completed

Critical blocker detected

Knowledge promoted

Market opportunity detected

Meeting scheduled

Executive approval required

Read-only.

7. Quick Actions

Buttons

New Client

Executive Briefing

Review Portfolio

Open CRM

Strategic Analysis

Start Meeting

View Projects

Generate Proposal

Company Health

Each routes to existing engines.

8. Search

Global search

Searches

Clients

Projects

Knowledge

Executives

Skills

Meetings

Proposals

Work Orders

Returns ranked results.

9. WebSocket Live Updates

Push updates for

Dashboard

Alerts

Projects

AI responses

Meetings

CRM

Portfolio

Knowledge

No polling.

10. Tests
NEW
tests/test_executive_console.py

Must verify:

Test	Validates
Dashboard loads	Dashboard renders correctly
Refresh	Refresh updates widgets
Assistant routing	Command bar routes to AI assistant
Activity feed	New events appear
Project loading	Projects displayed
Search	Finds expected entities
Quick actions	Trigger correct engine
Widget degradation	Missing engine doesn't crash UI
Dashboard serialization	View model serializes
Websocket updates	Events emitted correctly
Open Questions
1.

UI Framework

Recommendation:

React + TypeScript

Reason:

Already aligns with your CBT system and gives a modern SPA with reusable components.

2.

Backend Framework

Recommendation:

FastAPI

Reasons:

Lightweight
Async-ready
Automatic OpenAPI documentation
Excellent WebSocket support
Easy integration with your Python engine layer
3.

Charts

Recommendation:

Recharts
Tailwind CSS
shadcn/ui

These produce a professional executive dashboard with relatively little effort.

Verification Plan
Automated
python -m unittest discover -s tests

Expected:

All tests pass
Manual
Launch server.
Open Executive Console in a browser.
Verify dashboard loads.
Type "Good morning" into the command bar.
Confirm Executive Briefing appears.
Trigger "New Client".
Confirm AI Assistant orchestrates the workflow.
Verify activity feed updates.
Verify dashboard refreshes automatically.
Confirm no business logic resides in the UI layer.