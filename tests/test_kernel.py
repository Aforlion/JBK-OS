import unittest
import os
import shutil

from bootstrap import parse_yaml, locate_jbk_root, load_config, validate_environment, bootstrap
from runtime import Runtime


class TestKernel(unittest.TestCase):
    def test_yaml_parsing(self) -> None:
        yaml_content = """
# Test comment
name: "JBK OS Test"
version: 1.0
debug: true
nested:
  key: val
  number: 42
list_items:
  - first
  - second
"""
        parsed = parse_yaml(yaml_content)
        self.assertEqual(parsed["name"], "JBK OS Test")
        self.assertEqual(parsed["version"], 1.0)
        self.assertTrue(parsed["debug"])
        self.assertEqual(parsed["nested"]["key"], "val")
        self.assertEqual(parsed["nested"]["number"], 42)
        self.assertEqual(parsed["list_items"], ["first", "second"])

    def test_locate_jbk_root(self) -> None:
        root = locate_jbk_root()
        self.assertTrue(os.path.exists(os.path.join(root, "JBK-OS")))

    def test_load_config(self) -> None:
        root = locate_jbk_root()
        config = load_config(root)
        self.assertIn("company", config)
        self.assertIn("paths", config)
        self.assertIn("runtime", config)
        self.assertIn("logging", config)
        self.assertIn("skills", config)
        self.assertIn("executives", config)

    def test_validate_environment(self) -> None:
        root = locate_jbk_root()
        config = load_config(root)
        # Should not raise exception
        validate_environment(root, config)

    def test_successful_bootstrap(self) -> None:
        runtime = bootstrap()
        self.assertIsInstance(runtime, Runtime)
        self.assertEqual(runtime.status, "READY")
        
        # Verify registries are not empty (bypass in CI environment since JBK-Brain is a sibling folder not present in CI checkout)
        import os
        if os.environ.get("GITHUB_ACTIONS") != "true":
            self.assertGreater(len(runtime.worker_registry.list_workers()), 0)
            self.assertGreater(len(runtime.knowledge_registry.list_items()), 0)
            self.assertGreater(len(runtime.skill_registry.list_skills()), 0)
        
        # Verify console loads
        console_screen = runtime.executive_console.load()
        self.assertIn("Executive Briefing", console_screen)
        
        # Test command execution
        help_output = runtime.executive_console.execute_command("help")
        self.assertIn("Available commands:", help_output)
