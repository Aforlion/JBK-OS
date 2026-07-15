from __future__ import annotations

from typing import Any
import logging

LOGGER = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Any] = {}

    def register(self, skill: Any) -> Any:
        if skill is None:
            raise ValueError("Skill is required.")

        skill_id = getattr(skill, "skill_id", None) or getattr(skill, "id", None)
        if not skill_id:
            raise ValueError("Skill must have a valid ID.")

        if skill_id in self._skills:
            raise ValueError(f"Skill ID already registered: {skill_id}.")

        self._skills[skill_id] = skill
        LOGGER.info("object_id=%s action=register actor=system result=registered", skill_id)
        return skill

    def unregister(self, skill_id: str) -> Any:
        if not skill_id:
            raise ValueError("Skill ID is required.")

        if skill_id not in self._skills:
            raise ValueError(f"Skill ID is not registered: {skill_id}.")

        skill = self._skills.pop(skill_id)
        LOGGER.info("object_id=%s action=unregister actor=system result=unregistered", skill_id)
        return skill

    def find_by_id(self, skill_id: str) -> Any | None:
        if not skill_id:
            raise ValueError("Skill ID is required.")
        return self._skills.get(skill_id)

    def find_by_capability(self, capability: str) -> list[Any]:
        if not capability:
            raise ValueError("Capability is required.")

        cap_normalized = capability.strip().lower()
        matches = []
        for skill in self._skills.values():
            if hasattr(skill, "supports") and callable(skill.supports):
                if skill.supports(cap_normalized):
                    matches.append(skill)
            elif cap_normalized in [c.strip().lower() for c in getattr(skill, "capabilities", [])]:
                matches.append(skill)
        return matches

    def find_by_owner(self, owner_id: str) -> list[Any]:
        if not owner_id:
            raise ValueError("Owner ID is required.")

        return [
            skill
            for skill in self._skills.values()
            if getattr(skill, "owner_id", None) == owner_id
        ]

    def list_skills(self) -> list[Any]:
        return list(self._skills.values())

    def list_available(self) -> list[Any]:
        return [
            skill
            for skill in self._skills.values()
            if getattr(getattr(skill, "status", None), "value", getattr(skill, "status", None)) == "AVAILABLE"
        ]

    def summary(self) -> dict[str, Any]:
        skills_by_status: dict[str, int] = {}
        skills_by_department: dict[str, int] = {}

        for skill in self._skills.values():
            status = getattr(getattr(skill, "status", None), "value", getattr(skill, "status", "UNKNOWN"))
            skills_by_status[status] = skills_by_status.get(status, 0) + 1

            dept = getattr(skill, "department", "UNKNOWN")
            skills_by_department[dept] = skills_by_department.get(dept, 0) + 1

        return {
            "total_registered_skills": len(self._skills),
            "skills_by_status": skills_by_status,
            "skills_by_department": skills_by_department,
        }

    def to_dict(self) -> dict[str, Any]:
        serialized_skills = []
        for skill in self._skills.values():
            if hasattr(skill, "to_dict") and callable(skill.to_dict):
                serialized_skills.append(skill.to_dict())
            elif hasattr(skill, "__dict__"):
                serialized_skills.append(dict(skill.__dict__))
            else:
                serialized_skills.append(skill)

        return {
            "skills": serialized_skills,
            "summary": self.summary(),
        }
