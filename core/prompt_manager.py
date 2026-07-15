from __future__ import annotations

import os
import string
from typing import Any
import logging
from bootstrap import parse_yaml

LOGGER = logging.getLogger(__name__)

class PromptManager:
    """Manages versioned, parameterized templates out of inline business logic.

    Ensures prompt versioning, ownership tracking, and reuse across services.
    """

    def __init__(self, config_path: str | None = None) -> None:
        if not config_path:
            # Traverses to default directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "config", "prompts", "system_prompts.yaml")
        
        self.config_path = config_path
        self._prompts: dict[str, dict[str, Any]] = {}
        self.load_templates()

    def load_templates(self) -> None:
        """Loads prompt templates from config using basic YAML parser."""
        if not os.path.exists(self.config_path):
            LOGGER.warning("Prompt configuration file not found at: %s. Initiating empty templates.", self.config_path)
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Manual parse of simple prompts format
            self._prompts = {}
            current_id = None
            in_content = False
            content_lines = []

            for line in content.split('\n'):
                # Handle active content block
                if in_content:
                    if line.startswith("    ") or not line.strip():
                        # Standardize content lines removal of base indent
                        content_lines.append(line[6:] if len(line) >= 6 else "")
                        continue
                    else:
                        # Block finished
                        if current_id:
                            self._prompts[current_id]["content"] = '\n'.join(content_lines) + '\n'
                        in_content = False
                        content_lines = []
                        current_id = None

                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue

                if line.startswith("  ") and not line.startswith("    "):
                    # New prompt definition block
                    if ":" in stripped:
                        key = stripped.split(":", 1)[0].strip()
                        current_id = key
                        self._prompts[current_id] = {}
                elif line.startswith("    ") and not line.startswith("      ") and current_id:
                    if ":" in stripped:
                        k, v = stripped.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if v == "|":
                            in_content = True
                            content_lines = []
                        else:
                            self._prompts[current_id][k] = v.strip('"').strip("'")

            if in_content and current_id:
                self._prompts[current_id]["content"] = '\n'.join(content_lines) + '\n'

            LOGGER.info("Successfully loaded %d prompt templates.", len(self._prompts))
        except Exception as exc:
            LOGGER.error("Failed to parse prompt configuration: %s", exc, exc_info=True)
            self._prompts = {}


    def get_prompt_metadata(self, prompt_id: str) -> dict[str, Any]:
        """Returns metadata for a given prompt identifier."""
        prompt_data = self._prompts.get(prompt_id)
        if not prompt_data:
            raise KeyError(f"Prompt template '{prompt_id}' does not exist.")
        return {
            "version": prompt_data.get("version", "N/A"),
            "owner": prompt_data.get("owner", "N/A"),
            "description": prompt_data.get("description", "N/A")
        }

    def render(self, prompt_id: str, **kwargs: Any) -> str:
        """Renders prompt substituting parameters."""
        prompt_data = self._prompts.get(prompt_id)
        if not prompt_data:
            raise KeyError(f"Prompt template '{prompt_id}' does not exist.")

        template_str = prompt_data.get("content", "")
        # Standardize safe template substitution
        template = string.Template(template_str)
        # Default placeholder values to empty strings to avoid crashes
        safe_kwargs = {k: (v if v is not None else "") for k, v in kwargs.items()}
        return template.safe_substitute(safe_kwargs)
