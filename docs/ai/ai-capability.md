# AI Capability Guide — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** AI Integration Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [gemini-integration-architecture.md](gemini-integration-architecture.md)

---

## 1. Capabilities Overview

Gemini is registered as a native capability inside JBK-OS. Downstream engines request services by specifying a capability type rather than invoking a specific provider client directly.

Available capability types inside JBK-OS:
- `CHAT` (Standard conversational output)
- `REASONING` (Structured thinking and planning)
- `CODING` (Software engineering outputs)
- `RESEARCH` (Information extraction and analysis)
- `VISION` (Image parsing and description)
- `EMBEDDINGS` (Semantic vector generation)

---

## 2. Standardized Integration Interface

To invoke Gemini or any fallback provider, instantiate a standard `AIRequest` and dispatch it through the central gateway:

```python
from core.ai_gateway import AIGateway, AIRequest
from core.ai_provider import AICapability

# 1. Initialize Gateway
gateway = AIGateway()

# 2. Build Standardized Request
request = AIRequest(
    capability=AICapability.CHAT,
    prompt="Synthesize the operational parameters for the next release.",
    system_context="You are a Chief of Staff.",
    temperature=0.7,
    max_tokens=2048
)

# 3. Dispatched Execution
response = gateway.generate(request)

if response.success:
    print(f"Content: {response.content}")
    print(f"Source model: {response.model}")
else:
    print(f"Failed to execute: {response.routing_reason}")
```
