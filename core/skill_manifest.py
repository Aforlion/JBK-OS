from __future__ import annotations

from typing import Any


class SkillManifest:
    """Describes an executable skill's identity, capabilities, and runtime configuration (BR-038-002)."""

    def __init__(
        self,
        skill_id: str,
        name: str,
        version: str,
        owner: str,
        description: str,
        capabilities: list[str] | None = None,
        required_inputs: list[str] | None = None,
        generated_outputs: list[str] | None = None,
        supported_models: list[str] | None = None,
        quality_validator: str | None = None,
        changelog: list[str] | None = None,
    ) -> None:
        if not skill_id:
            raise ValueError("Skill ID is required.")
        if not name:
            raise ValueError("Skill name is required.")
        if not version:
            raise ValueError("Skill version is required.")

        self.skill_id = skill_id
        self.name = name
        self.version = version
        self.owner = owner
        self.description = description
        self.capabilities = list(capabilities or [])
        self.required_inputs = list(required_inputs or [])
        self.generated_outputs = list(generated_outputs or [])
        self.supported_models = list(supported_models or [])
        self.quality_validator = quality_validator or "default"
        self.changelog = list(changelog or [])

    def summary(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "capabilities": list(self.capabilities),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "owner": self.owner,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "required_inputs": list(self.required_inputs),
            "generated_outputs": list(self.generated_outputs),
            "supported_models": list(self.supported_models),
            "quality_validator": self.quality_validator,
            "changelog": list(self.changelog),
        }
