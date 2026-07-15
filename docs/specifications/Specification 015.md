# JBK OS

# Specification 015

## Title

Knowledge Registry

---

## Version

1.0

---

## Status

Approved

---

# Purpose

The Knowledge Registry is the central discovery service for all organizational knowledge within JBK OS.

It enables executives, workflows, planners, and future AI agents to locate relevant knowledge without needing to know where it is physically stored.

The Knowledge Registry is an index, not a knowledge repository.

---

# Responsibilities

The Knowledge Registry shall:

* Register knowledge assets.
* Discover knowledge by topic.
* Discover knowledge by category.
* Discover knowledge by owner.
* Discover knowledge by tags.
* Report knowledge availability.
* Maintain metadata only.

---

# Dependencies

The Knowledge Registry depends on:

* KnowledgeItem
* Standard Python Library

It shall not depend on:

* Chief of Staff
* Executive Workspace
* Execution Planner
* Execution Engine

---

# Core Objects

## KnowledgeItem

Required fields:

* knowledge_id
* title
* category
* owner
* source
* tags
* description
* version
* status
* created_at
* updated_at

---

## KnowledgeStatus

Required values:

* ACTIVE
* ARCHIVED
* DEPRECATED
* DRAFT

---

# Required Methods

KnowledgeItem

* summary()
* to_dict()
* matches(query)

KnowledgeRegistry

* register(item)
* unregister(knowledge_id)
* find_by_id(knowledge_id)
* find_by_category(category)
* find_by_owner(owner)
* find_by_tag(tag)
* search(query)
* list_items()
* summary()
* to_dict()

---

# Architectural Principles

The Knowledge Registry:

* Stores metadata only.
* Does not store document contents.
* Does not perform AI reasoning.
* Does not execute workflows.
* Does not modify registered documents.

---

# Business Rules

BR-0024

Duplicate Knowledge IDs are prohibited.

BR-0025

Knowledge Items may contain multiple tags.

BR-0026

Search operations are read-only.

BR-0027

Archived knowledge remains discoverable unless explicitly removed.

---

# Architectural Constraints

The registry:

* Owns no business objects.
* Owns no projects.
* Owns no work orders.
* Owns no skills.
* Owns no execution logic.

---

# Non Goals

Version 1 excludes:

* Vector databases
* Semantic search
* Embeddings
* AI summarization
* Automatic indexing
* External document storage

---

# Acceptance Criteria

The implementation shall:

* Register Knowledge Items.
* Reject duplicate IDs.
* Search by category.
* Search by owner.
* Search by tags.
* Perform keyword search.
* Produce summaries.
* Pass all unit tests.

---

# Future Evolution

Future versions may support:

* Semantic search
* Embedding indexes
* Automatic document ingestion
* Knowledge ranking
* Executive recommendations
* Client-specific knowledge spaces
* Learning from completed projects

---

# Definition of Done

* KnowledgeItem implemented.
* KnowledgeRegistry implemented.
* Unit tests pass.
* Ready for integration with the JBK Brain.
