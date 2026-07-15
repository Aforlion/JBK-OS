Specification 043 — Client Success & Support Engine
Goal

Create the engine responsible for the entire post-delivery customer lifecycle.

It continuously monitors every completed client engagement and recommends actions that improve retention, satisfaction, renewals, referrals and upsells.

It never contacts clients automatically.

It only advises executives.

New Models
core/client_success_plan.py

ClientSuccessPlan

SupportSchedule

SuccessMilestone

RenewalOpportunity

UpsellOpportunity

RiskAlert
core/client_success_report.py

ClientSuccessReport
Engine
core/client_success_engine.py

Main class

ClientSuccessEngine

Input

ClientProfile

CRMReport

ProjectClosureReport

KnowledgeRegistry

Output

ClientSuccessReport
Responsibilities
1.

Determine overall customer success status

Possible values

ONBOARDING

ACTIVE

ADOPTION

STABLE

AT_RISK

ADVOCATE

LOST
2.

Recommend support schedule

Example

Weekly

Monthly

Quarterly

Annual
3.

Detect renewal opportunities

For example

Support contract ending

License renewal

Maintenance renewal

Training renewal
4.

Detect upsell opportunities

Examples

AI Automation

Analytics Dashboard

Executive Training

Additional Department Automation

Maintenance Package
5.

Measure relationship trend

Improving

Stable

Declining
6.

Generate executive recommendations

Example

Schedule quarterly review.

Recommend executive visit.

Offer maintenance package.

Offer AI optimisation audit.

Nominate client for referral program.
7.

Risk Detection

Examples

No interaction for 90 days

Declining relationship health

Open support issues

Rejected proposal history

Late payments
8.

Knowledge Capture

Register

KnowledgeItem

summarizing

What keeps this client successful?
Decision Boundaries

The engine may NEVER

send emails
call clients
renew contracts
invoice clients
change CRM records

It is advisory only.

Tests

Create

tests/test_client_success_engine.py

Verify

customer lifecycle state
renewal detection
upsell detection
support scheduling
risk alerts
recommendation generation
advisory boundary
knowledge registration
serialization
Brain Entry

Create

JBK-Brain/
Architecture/
Client-Success-Standards.md

Standards

Never automatically contact customers.

Every recommendation must include reasoning.

Every client should always have a next recommended engagement.

Capture success patterns into the Knowledge Registry.