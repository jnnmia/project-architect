#!/usr/bin/env python3
"""Unit test suite for Project Architect scaffolder and rule injector."""

import contextlib
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for direct import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import scaffold_rules

SKILL_ROOT = Path(__file__).resolve().parent.parent


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

    def test_inject_adversarial_arabic_numerals(self):
        """Adversarial Test: Principles numbered with Arabic numerals (1., 2.)."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# Custom Constitution\n\n"
            "## Core Principles\n\n"
            "### 1. 架构分层设计\n"
            "- 业务逻辑 MUST 与展示层严格解耦。\n"
            "### 2. 自动化测试底线\n"
            "- 核心接口变更 必须 具备自动化单测覆盖。\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code, 0)

        claude_content = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("#### 1. 架构分层设计", claude_content)
        self.assertIn("业务逻辑 MUST 与展示层严格解耦。", claude_content)
        self.assertIn("#### 2. 自动化测试底线", claude_content)
        self.assertIn("核心接口变更 必须 具备自动化单测覆盖。", claude_content)
        self.assertNotIn("Refer to rules document for binding MUST/SHOULD principles", claude_content)

    def test_inject_adversarial_chinese_numerals(self):
        """Adversarial Test: Principles numbered with Chinese characters (原则一, 原则二)."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# 宪法规范\n\n"
            "## 核心原则\n\n"
            "### 原则一：零第三方依赖\n"
            "- 优先使用 Python 3 标准库。\n"
            "### 原则二：零内网信息外泄\n"
            "- 严禁 在公开代码中包含内网域名。\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "agents"])
        self.assertEqual(exit_code, 0)

        agents_content = (self.test_dir / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("#### 原则一：零第三方依赖", agents_content)
        self.assertIn("优先使用 Python 3 标准库。", agents_content)
        self.assertIn("#### 原则二：零内网信息外泄", agents_content)
        self.assertIn("严禁 在公开代码中包含内网域名。", agents_content)

    def test_inject_adversarial_roman_beyond_five(self):
        """Adversarial Test: Principles with Roman numerals > V (VI., X.)."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# Scaled Constitution\n\n"
            "## Core Principles\n\n"
            "### VI. 性能指标基线\n"
            "- P99 接口耗时 MUST 小于 100ms。\n"
            "### X. 容灾熔断策略\n"
            "- 服务调用 MUST 具备重试上限与超时控制。\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code, 0)

        claude_content = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("#### VI. 性能指标基线", claude_content)
        self.assertIn("P99 接口耗时 MUST 小于 100ms。", claude_content)
        self.assertIn("#### X. 容灾熔断策略", claude_content)
        self.assertIn("服务调用 MUST 具备重试上限与超时控制。", claude_content)

    def test_inject_adversarial_unnumbered_titles(self):
        """Adversarial Test: Principles with unnumbered plain headings."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# Constitution\n\n"
            "## Core Principles\n\n"
            "### Architectural Decoupling\n"
            "- Components MUST expose clear public contracts.\n"
            "### Fail Fast and Gracefully\n"
            "- Unknown inputs SHOULD be rejected immediately.\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code, 0)

        claude_content = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("#### Architectural Decoupling", claude_content)
        self.assertIn("Components MUST expose clear public contracts.", claude_content)
        self.assertIn("#### Fail Fast and Gracefully", claude_content)
        self.assertIn("Unknown inputs SHOULD be rejected immediately.", claude_content)

    def test_inject_adversarial_scope_isolation(self):
        """Adversarial Test: Does not extract subsections from Overview or Workflow."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# Constitution\n\n"
            "## Overview\n\n"
            "### Project Goals\n"
            "- We MUST finish by end of week.\n\n"
            "## Core Principles\n\n"
            "### 1. True Principle\n"
            "- Production code MUST have unit tests.\n\n"
            "## Development Workflow & Checkpoints\n\n"
            "### Review Gate\n"
            "- PR MUST be reviewed.\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code, 0)

        claude_content = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("#### 1. True Principle", claude_content)
        self.assertIn("Production code MUST have unit tests.", claude_content)
        # Verify non-principles sections are NOT extracted
        self.assertNotIn("Project Goals", claude_content)
        self.assertNotIn("Review Gate", claude_content)

    def test_inject_adversarial_filters_rationales(self):
        """Adversarial Test: Rationale paragraphs are excluded from rule list."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        const_file.write_text(
            "# Constitution\n\n"
            "## Core Principles\n\n"
            "### 1. Minimal Complexity\n"
            "- YAGNI: Do not implement unrequested features.\n"
            "*Rationale:* Premature abstraction increases maintenance burden.\n"
            "- Keep code simple.\n",
            encoding="utf-8"
        )
        exit_code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code, 0)

        claude_content = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("YAGNI: Do not implement unrequested features.", claude_content)
        self.assertIn("Keep code simple.", claude_content)
        self.assertNotIn("Premature abstraction", claude_content)

    def test_inject_adversarial_strict_mode(self):
        """Adversarial Test: --strict flag halts with exit code 1 when 0 principles found."""
        mem_dir = self.test_dir / ".specify" / "memory"
        mem_dir.mkdir(parents=True, exist_ok=True)
        const_file = mem_dir / "constitution.md"
        # Constitution without any principles
        const_file.write_text("# Empty Constitution\n## Overview\nNo principles here.\n", encoding="utf-8")

        # Without strict, injects fallback and exits 0
        exit_code_normal = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        self.assertEqual(exit_code_normal, 0)

        # With strict, fails with exit code 1
        exit_code_strict = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude", "--strict"])
        self.assertEqual(exit_code_strict, 1)


class QuietResult:
    """Run a callable with stdout/stderr captured and report (exit_code, out, err)."""

    @staticmethod
    def run(func, *args, **kwargs):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = func(*args, **kwargs)
        return code, out.getvalue(), err.getvalue()


class TestDeterministicOutput(unittest.TestCase):
    """Generated files must be byte-identical across platforms (UTF-8, LF only)."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _init_project(self):
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])

    def _inject(self, agents):
        return scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", agents])

    GENERATED = [
        ".specify/memory/constitution.md",
        "templates/plan-template.md",
        "templates/spec-template.md",
        "templates/tasks-template.md",
        "AGENTS.md",
        "CLAUDE.md",
        ".cursor/rules/project-rules.mdc",
    ]

    def test_generated_files_contain_no_carriage_returns(self):
        """Regression: Windows text-mode writes used to emit CRLF everywhere."""
        self._init_project()
        self._inject("agents,claude,cursor")

        for rel in self.GENERATED:
            with self.subTest(file=rel):
                raw = (self.test_dir / rel).read_bytes()
                self.assertNotIn(b"\r", raw, f"{rel} contains CR bytes; output is not LF-only")

    def test_preexisting_crlf_content_is_normalised(self):
        """A hand-edited CRLF context file is rewritten with LF, keeping user text."""
        self._init_project()
        self.test_dir.joinpath("CLAUDE.md").write_bytes(
            "# User Notes\r\n- keep me\r\n".encode("utf-8")
        )
        code = self._inject("claude")
        self.assertEqual(code, 0)

        raw = (self.test_dir / "CLAUDE.md").read_bytes()
        self.assertNotIn(b"\r", raw)
        text = raw.decode("utf-8")
        self.assertIn("# User Notes", text)
        self.assertIn("- keep me", text)

    def test_leading_bom_is_stripped(self):
        """A BOM written by a Windows editor must not survive into generated output."""
        self._init_project()
        self.test_dir.joinpath("CLAUDE.md").write_bytes(
            "\ufeff# User Notes\n".encode("utf-8")
        )
        code = self._inject("claude")
        self.assertEqual(code, 0)

        text = (self.test_dir / "CLAUDE.md").read_bytes().decode("utf-8")
        self.assertNotIn("\ufeff", text)
        self.assertTrue(text.startswith("# User Notes"))

    def test_non_utf8_target_reports_exit_code_2(self):
        """Legacy CP936 content yields a clean exit code, never a traceback."""
        self._init_project()
        self.test_dir.joinpath("CLAUDE.md").write_bytes("中文说明".encode("gbk"))

        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
        )
        self.assertEqual(code, 2)
        self.assertIn("not valid UTF-8", err)

    def test_missing_asset_template_reports_actionable_error(self):
        """A partially copied skill must explain itself instead of raising FileNotFoundError."""
        with self.assertRaises(scaffold_rules.RuleIOError) as ctx:
            scaffold_rules._load_asset_template("does-not-exist.md")
        self.assertIn("assets/templates", str(ctx.exception))
        self.assertIn("skills add", str(ctx.exception))

    def test_shared_helpers_round_trip(self):
        """write_text/read_text normalise newlines and emit UTF-8 without a BOM."""
        target = self.test_dir / "nested" / "deep" / "out.md"
        scaffold_rules.write_text(target, "a\r\nb\rc\n")
        raw = target.read_bytes()
        self.assertEqual(raw, b"a\nb\nc\n")
        self.assertEqual(scaffold_rules.read_text(target), "a\nb\nc\n")


class TestAgentKeyValidation(unittest.TestCase):
    """A rejected agent target must be an error signal, not a silent warning."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_typo_in_agent_list_fails_but_keeps_valid_targets(self):
        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude,curor"]
        )
        self.assertEqual(code, 1)
        self.assertIn("Unknown agent key: 'curor'", err)
        # The valid target is still written, so a single typo does not lose work.
        self.assertTrue((self.test_dir / "CLAUDE.md").exists())
        self.assertFalse((self.test_dir / ".cursor" / "rules" / "project-rules.mdc").exists())

    def test_all_unknown_agent_keys_fail_and_write_nothing(self):
        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "bogus"]
        )
        self.assertEqual(code, 1)
        self.assertIn("No agent context file was updated", err)
        self.assertFalse((self.test_dir / "CLAUDE.md").exists())

    def test_empty_agent_list_fails(self):
        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "  ,  "]
        )
        self.assertEqual(code, 1)
        self.assertIn("No agent context file was updated", err)


class TestDocumentationContract(unittest.TestCase):
    """Guard the class of bug where docs drift away from the on-disk layout."""

    def test_skill_md_has_no_collection_layout_path(self):
        """SKILL.md must not hardcode an install prefix such as skills/<name>/scripts/."""
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("skills/project-architect/scripts/", text)

    def test_skill_md_documented_script_path_exists(self):
        """Every scripts/scaffold_rules.py reference must resolve from the skill root."""
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/scaffold_rules.py", text)
        self.assertTrue((SKILL_ROOT / "scripts" / "scaffold_rules.py").is_file())

    def test_skill_md_documents_the_exit_code_contract(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("退出码契约", text)

    def test_shipped_templates_do_not_reference_the_skill_script(self):
        """Templates are copied into user projects, where this script does not exist."""
        for template in sorted((SKILL_ROOT / "assets" / "templates").glob("*.md")):
            with self.subTest(template=template.name):
                self.assertNotIn("scaffold_rules.py", template.read_text(encoding="utf-8"))


    def test_readme_trees_only_name_files_that_exist(self):
        """Guards the drift where both README trees advertised a nonexistent README.en.md."""
        name_pattern = re.compile(r"\bREADME(?:\.zh-CN|\.en)?\.md\b")
        for doc in ("README.md", "README.zh-CN.md"):
            text = (SKILL_ROOT / doc).read_text(encoding="utf-8")
            # Inspect only the directory-tree block; prose links are not file claims.
            blocks = text.split("```text")
            tree = blocks[-1].split("```", 1)[0] if len(blocks) > 1 else ""
            for name in sorted(set(name_pattern.findall(tree))):
                with self.subTest(doc=doc, name=name):
                    self.assertTrue(
                        (SKILL_ROOT / name).is_file(),
                        f"{doc} tree lists {name}, which does not exist",
                    )


    def test_pyproject_declares_no_console_script(self):
        """Regression: a 'project-architect' entry point was declared but could never install."""
        text = (SKILL_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertNotIn("[project.scripts]", text)
        self.assertNotIn("scripts.scaffold_rules:main", text)

    def test_declared_version_matches_skill_metadata(self):
        """A release must bump the version in pyproject.toml and SKILL.md together."""
        pyproject = (SKILL_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        pyproject_version = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject)
        skill_version = re.search(r'(?m)^\s*version\s*:\s*"([^"]+)"', skill_md)
        self.assertIsNotNone(pyproject_version, "no version found in pyproject.toml")
        self.assertIsNotNone(skill_version, "no version found in SKILL.md metadata")

        self.assertEqual(pyproject_version.group(1), skill_version.group(1))


if __name__ == "__main__":
    unittest.main()
