Specification 042 — Organizational Memory & Context Engine

This is one of the most important specifications in the entire system.

Without it, JBK-OS forgets.

With it...

JBK-OS becomes an organization that remembers everything.

Goal

Create the Organizational Memory Engine responsible for building persistent organizational memory across every interaction.

Instead of simply storing Knowledge Items, the company should remember:

clients
meetings
conversations
proposals
failures
decisions
negotiations
executive preferences
project history
lessons
recurring patterns

Exactly like an experienced executive would.

New Components
1. MemoryRecord
core/memory_record.py

Represents one memory.

Fields

id
category
title
summary
full_context
related_entities
created_by
created_at
confidence
importance
tags
source_engine
2. MemoryRegistry
core/memory_registry.py

Unlike KnowledgeRegistry...

Knowledge Registry stores documents.

Memory Registry stores experiences.

Functions

register()

search()

find_related()

find_recent()

find_by_client()

find_by_project()

find_by_tag()

summarize()

archive()
3. OrganizationalMemoryEngine
core/organizational_memory_engine.py

This engine automatically receives outputs from every other engine.

Examples

Opportunity created

↓

Remember

Proposal rejected

↓

Remember why

Client negotiated pricing

↓

Remember pricing preference

Project delayed

↓

Remember root cause

CEO rejected proposal

↓

Remember decision rationale

Meeting produced action items

↓

Remember commitments

Knowledge generated

↓

Create memory linking to knowledge

Automatic Context Building

Every future conversation begins by asking:

"What do we already know?"

For example

CEO asks

"We have another school."

Assistant automatically recalls

We have delivered three school automation projects.

Average duration:
8 weeks

Most requested feature:
HR automation

Typical budget:
$18,000

Biggest previous mistake:
Parent portal delayed due to integration complexity.

Recommendation:
Reuse School Automation Blueprint Version 3.

No manual lookup.

No prompt engineering.

Organizational memory.

Relationship Graph

Every memory should link to other objects.

Example

Client

↓

Proposal

↓

Meeting

↓

Project

↓

Work Orders

↓

Lessons Learned

↓

Knowledge

↓

Future Proposal


Nothing becomes isolated.

Retrieval Ranking

Not every memory is equally important.

Ranking factors

recency
importance
success
frequency
executive decisions
client importance
Explainability

Every retrieved memory must answer

Why was this shown?

Example

Retrieved because:

✓ Same client

✓ Same industry

✓ Similar problem

✓ Referenced in previous meeting

Confidence

96%
Business Rules
BR-042-001

Every completed engine may generate memories.

BR-042-002

Memory never replaces Knowledge.

BR-042-003

Memories maintain relationships.

BR-042-004

Every memory has confidence.

BR-042-005

Every memory is explainable.

BR-042-006

Nothing is automatically deleted.

Only archived.

BR-042-007

Duplicate memories merge.

BR-042-008

Memory retrieval is relevance-ranked.

BR-042-009

Client history is always searchable.

BR-042-010

Memories can reference Knowledge Items.

Future Evolution

Version 2+

Vector semantic search
Local embedding database
Hybrid keyword + embedding retrieval
Timeline visualization of organizational history
Executive memory heatmaps
Automatic memory summarization
Client relationship intelligence
Memory decay and reinforcement algorithms
Cross-client pattern detection
"What would we do differently?" recommendation engine based on historical outcomes
Candidate Brain Entry

Organizational-Memory-Standards.md

All organizational memory systems must satisfy:

1. Memory captures experiences, not documents.

2. Every memory must explain why it was retrieved.

3. Memories are never deleted automatically.

4. Every memory links to organizational entities.

5. Duplicate memories merge rather than multiply.

6. Memory strengthens organizational intelligence over time.