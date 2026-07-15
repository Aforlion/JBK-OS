# Prompt Management Guide — JBK-OS

**Work Order:** OL-0005
**Category:** Project-Memory
**Owner:** AI Integration Engineer
**Status:** Active
**Created:** 2026-07-15
**Review Date:** 2027-07-15
**Related:** [gemini-integration-architecture.md](gemini-integration-architecture.md)

---

## 1. Centralized Prompt Management

To prevent large system prompts from cluttering business logic, JBK-OS utilizes a centralized template registry located in `config/prompts/system_prompts.yaml`. 

This configuration separates prompt authorship, ownership, and versioning from functional application code.

---

## 2. Registry Structure

Prompts are declared in `config/prompts/system_prompts.yaml` using the following schema:

```yaml
prompts:
  template_identifier:
    version: "1.0.0"
    owner: "DepartmentRole"
    description: "Brief functional explanation"
    content: |
      System instructions go here.
      You can use variables like $variable_name for dynamic substitution.
```

---

## 3. Invoking the Prompt Manager

The `PromptManager` class (`core/prompt_manager.py`) is responsible for reading YAML templates, rendering parameters, and returning fully formed prompts:

```python
from core.prompt_manager import PromptManager

# Instantiate Prompt Manager
manager = PromptManager()

# Retrieve metadata
meta = manager.get_prompt_metadata("coding_assistant")
print(f"Using template version: {meta['version']} owned by {meta['owner']}")

# Render template with variables
rendered_prompt = manager.render(
    "coding_assistant",
    task_description="Implement a JWT authentication decorator."
)
```
