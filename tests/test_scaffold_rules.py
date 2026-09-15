#!/usr/bin/env python3
"""Unit test suite for Project Architect scaffolder and rule injector."""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for direct import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import scaffold_rules


class TestScaffoldRules(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_all_expected_files(self):
        """Verify init creates constitution, templates and baseline AGENTS.md."""
        exit_code = scaffold_rules.main([
            "init",
            "--dir", str(self.test_dir),
            "--name", "demo-cli",
            "--purpose", "Test CLI Utility"
        ])
        self.assertEqual(exit_code, 0)

        const_file = self.test_dir / ".specify" / "memory" / "constitution.md"
        self.assertTrue(const_file.exists())
        content = const_file.read_text(encoding="utf-8")
        self.assertIn("# demo-cli Constitution", content)
        self.assertIn("Test CLI Utility", content)
        self.assertNotIn("[PROJECT_NAME]", content)

        self.assertTrue((self.test_dir / "templates" / "plan-template.md").exists())
        self.assertTrue((self.test_dir / "templates" / "spec-template.md").exists())
        self.assertTrue((self.test_dir / "templates" / "tasks-template.md").exists())
        self.assertTrue((self.test_dir / "AGENTS.md").exists())

    def test_init_idempotency_preserves_modifications_unless_forced(self):
        """Verify init does not overwrite modified constitution without --force."""
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "my-app"])
        const_file = self.test_dir / ".specify" / "memory" / "constitution.md"

        custom_text = "# Custom Edited Constitution Content"
        const_file.write_text(custom_text, encoding="utf-8")

        # Run init again without force
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "my-app"])
        self.assertEqual(const_file.read_text(encoding="utf-8"), custom_text)

        # Run init with --force
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "my-app", "--force"])
        self.assertNotEqual(const_file.read_text(encoding="utf-8"), custom_text)

    def test_inject_preserves_external_user_content(self):
        """Verify inject updates only content between boundary markers."""
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "tool-x"])

        claude_file = self.test_dir / "CLAUDE.md"
        pre_existing = "# User Custom Commands\n- run: pytest -v\n"
        claude_file.write_text(pre_existing, encoding="utf-8")

        exit_code = scaffold_rules.main([
            "inject",
            "--dir", str(self.test_dir),
            "--agents", "claude,cursor"
        ])
        self.assertEqual(exit_code, 0)

        updated_claude = claude_file.read_text(encoding="utf-8")
        self.assertTrue(updated_claude.startswith("# User Custom Commands"))
        self.assertIn(scaffold_rules.DEFAULT_START_MARKER, updated_claude)
        self.assertIn(scaffold_rules.DEFAULT_END_MARKER, updated_claude)
        self.assertIn("Project Governance & Principles (Automated)", updated_claude)

        # Ensure Cursor MDC has frontmatter
        cursor_file = self.test_dir / ".cursor" / "rules" / "project-rules.mdc"
        self.assertTrue(cursor_file.exists())
        cursor_content = cursor_file.read_text(encoding="utf-8")
        self.assertIn("alwaysApply: true", cursor_content)

    def test_marker_single_sided_recovery(self):
        """Verify injector safely recovers when only start marker or only end marker exists."""
        target_file = self.test_dir / "TEST_RULES.md"

        # Case: Only start marker exists
        target_file.write_text("Prefix\n<!-- RULES START -->\nOld content\n", encoding="utf-8")
        scaffold_rules._upsert_marker_section(
            target_file,
            "<!-- RULES START -->",
            "<!-- RULES END -->",
            "New Valid Rules"
        )
        content = target_file.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("Prefix\n<!-- RULES START -->"))
        self.assertIn("New Valid Rules", content)
        self.assertIn("<!-- RULES END -->", content)

        # Case: Only end marker exists
        target_file.write_text("Old Header\n<!-- RULES END -->\nTrailing suffix", encoding="utf-8")
        scaffold_rules._upsert_marker_section(
            target_file,
            "<!-- RULES START -->",
            "<!-- RULES END -->",
            "Replacement Block"
        )
        content2 = target_file.read_text(encoding="utf-8")
        self.assertIn("<!-- RULES START -->", content2)
        self.assertIn("Replacement Block", content2)
        self.assertTrue(content2.endswith("Trailing suffix"))

    def test_validate_detects_unresolved_placeholders(self):
        """Verify validate fails when unresolved placeholders remain."""
        scaffold_rules.main(["init", "--dir", str(self.test_dir)])
        const_file = self.test_dir / ".specify" / "memory" / "constitution.md"

        # Inject an unresolved placeholder
        content = const_file.read_text(encoding="utf-8")
        content += "\n- Rule: [UNRESOLVED_PLACEHOLDER] must be set."
        const_file.write_text(content, encoding="utf-8")

        exit_code = scaffold_rules.main(["validate", "--dir", str(self.test_dir)])
        self.assertEqual(exit_code, 1)

    def test_validate_passes_for_initialized_constitution(self):
        """Verify default initialized constitution passes validation."""
        scaffold_rules.main([
            "init",
            "--dir", str(self.test_dir),
            "--name", "valid-proj",
            "--purpose", "Valid Test Project"
        ])
        exit_code = scaffold_rules.main(["validate", "--dir", str(self.test_dir)])
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
