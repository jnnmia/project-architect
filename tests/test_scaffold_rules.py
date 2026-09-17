#!/usr/bin/env python3
"""Unit test suite for Project Architect scaffolder and rule injector."""

import contextlib
import io
import os
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
        # The default constitution template is Chinese, so the generated block
        # must frame itself in Chinese rather than in English boilerplate.
        self.assertIn("## 项目治理与核心原则（自动生成）", updated_claude)

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


class TestDetectCommand(unittest.TestCase):
    """detect gathers evidence about which tools a project uses; it must never write."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @staticmethod
    def _snapshot(root: Path):
        return sorted(str(p.relative_to(root)) for p in root.rglob("*"))

    def test_empty_project_reports_nothing_and_fails(self):
        """A brand-new project has no traces, so the caller must go ask the user."""
        code, out, err = QuietResult.run(
            scaffold_rules.main, ["detect", "--dir", str(self.test_dir)]
        )
        self.assertEqual(code, 1)
        # Not [FAIL]: a brand-new project is a normal outcome, not a broken one.
        self.assertNotIn("[FAIL]", err)
        self.assertIn("[NOTICE]", err)
        self.assertIn("ask the user which tools they use", err)
        for agent in scaffold_rules.AGENT_TARGET_MAP:
            self.assertIn(agent, out)

    def test_missing_directory_is_an_io_error(self):
        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["detect", "--dir", str(self.test_dir / "nope")]
        )
        self.assertEqual(code, 2)
        self.assertIn("does not exist", err)

    def test_detects_only_tools_with_evidence(self):
        self.test_dir.joinpath(".cursor", "rules").mkdir(parents=True)
        self.test_dir.joinpath("CLAUDE.md").write_text("# x\n", encoding="utf-8")

        code, out, err = QuietResult.run(
            scaffold_rules.main, ["detect", "--dir", str(self.test_dir)]
        )
        self.assertEqual(code, 0)
        detected = scaffold_rules.detect_agent_signatures(self.test_dir)
        self.assertEqual(sorted(detected), ["claude", "cursor"])
        # Tools with no on-disk trace must not be reported as present.
        self.assertNotIn("windsurf", detected)
        self.assertIn("windsurf", out)  # still listed, as "no trace"
        self.assertIn("[no trace]", out)

    def test_detect_writes_nothing(self):
        self.test_dir.joinpath(".cursor", "rules").mkdir(parents=True)
        before = self._snapshot(self.test_dir)
        scaffold_rules.main(["detect", "--dir", str(self.test_dir)])
        self.assertEqual(before, self._snapshot(self.test_dir))

    def test_deep_directory_hit_is_reported(self):
        """A nested project keeps its signatures relative to the scanned root."""
        nested = self.test_dir / "service"
        nested.joinpath(".windsurf").mkdir(parents=True)
        detected = scaffold_rules.detect_agent_signatures(nested)
        self.assertEqual(sorted(detected), ["windsurf"])


class TestAgentTargetSelection(unittest.TestCase):
    """The injected target set must be an explicit, confirmed subset."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_inject_without_agents_is_a_usage_error(self):
        """Regression: --agents used to default to 'agents,claude,cursor'."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                scaffold_rules.main(["inject", "--dir", str(self.test_dir)])
        self.assertEqual(ctx.exception.code, 2)

    def test_unconfirmed_tools_are_never_written(self):
        """Regression: all supported tools used to be injected in one go."""
        code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "agents,claude"])
        self.assertEqual(code, 0)

        self.assertTrue((self.test_dir / "AGENTS.md").exists())
        self.assertTrue((self.test_dir / "CLAUDE.md").exists())
        for rel in [".cursor", ".windsurf", ".trae", "GEMINI.md", ".github"]:
            with self.subTest(path=rel):
                self.assertFalse(
                    (self.test_dir / rel).exists(),
                    f"{rel} was created for a tool the caller did not ask for",
                )

    def test_injecting_every_supported_tool_is_not_the_default_path(self):
        """The full set stays reachable, but only when spelled out explicitly."""
        everything = ",".join(scaffold_rules.AGENT_TARGET_MAP)
        code = scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", everything])
        self.assertEqual(code, 0)
        for agent, rel in scaffold_rules.AGENT_TARGET_MAP.items():
            with self.subTest(agent=agent):
                self.assertTrue((self.test_dir / rel).exists())


    def test_skill_md_gates_injection_on_tool_confirmation(self):
        """The contract must require detect-then-confirm instead of blanket injection."""
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("detect", text)
        self.assertIn("禁止全量注入", text)
        self.assertIn("没有默认值", text)

    def test_documented_agent_sets_stay_narrow(self):
        """No doc should demonstrate a blanket injection of every supported target."""
        pattern = re.compile(r'--agents\s+"([^"]+)"')
        for doc in ("SKILL.md", "README.md", "README.zh-CN.md"):
            text = (SKILL_ROOT / doc).read_text(encoding="utf-8")
            for value in pattern.findall(text):
                keys = [k.strip() for k in value.split(",") if k.strip()]
                with self.subTest(doc=doc, value=value):
                    self.assertLessEqual(
                        len(keys),
                        3,
                        f"{doc} demonstrates injecting {len(keys)} targets; "
                        "documented examples must stay a confirmed subset",
                    )


class TestAdversarialHardening(unittest.TestCase):
    """Defects surfaced by the adversarial audit; each test is a live scoreboard."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))

    def tearDown(self):
        for root, _dirs, files in os.walk(self.test_dir):
            for name in files:
                try:
                    os.chmod(os.path.join(root, name), 0o644)
                except OSError:
                    pass
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _write_constitution(self, body: str) -> Path:
        mem = self.test_dir / ".specify" / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        const = mem / "constitution.md"
        const.write_text(body, encoding="utf-8")
        return const

    # -- determinism -------------------------------------------------------
    def test_placeholder_message_is_deterministic(self):
        """Regression: the dedupe iterated a set, so order followed PYTHONHASHSEED."""
        const = self.test_dir / ".specify" / "memory" / "constitution.md"
        self.test_dir.joinpath(".specify", "memory").mkdir(parents=True)
        const.write_text(
            "# C\n\n## Overview\n\n1.0.0\n\n## Core Principles\n\n### P\n"
            "- A MUST [AAA_TOKEN]\n- B MUST [BBB_TOKEN]\n- C MUST [CCC_TOKEN]\n"
            "- D MUST [DDD_TOKEN]\n- E MUST [AAA_TOKEN]\n",
            encoding="utf-8",
        )
        runs = set()
        for _ in range(5):
            code, out, _err = QuietResult.run(
                scaffold_rules.main, ["validate", "--dir", str(self.test_dir)]
            )
            line = [l for l in out.splitlines() if "Unresolved" in l]
            self.assertTrue(line, "expected a placeholder error line")
            if code != 1:
                # A wrong validate outcome would make the ordering check moot.
                self.fail(f"validate unexpectedly returned {code}")
            runs.add(line[0])
        self.assertEqual(len(runs), 1, f"message is not deterministic: {runs}")

        # strip() drops validate's own "  - " bullet prefix from the report.
        message = runs.pop().strip().lstrip("-").strip()
        expected = "Unresolved placeholders found: [AAA_TOKEN], [BBB_TOKEN], [CCC_TOKEN], [DDD_TOKEN]"
        self.assertEqual(message, expected)

    # -- validate false positives -----------------------------------------
    def test_common_bracket_words_are_not_placeholders(self):
        """Regression: [TODO]/[NOTE] in prose failed validation as unfilled slots."""
        const = self.test_dir / ".specify" / "memory" / "constitution.md"
        self.test_dir.joinpath(".specify", "memory").mkdir(parents=True)
        const.write_text(
            "# C\n\n## Overview\n1.0.0\n\n## Core Principles\n\n### P\n"
            "- 状态参见 [TODO] 与 [NOTE] 表，标记见 [IMPORTANT]。\n"
            "- 所有变更 MUST 伴随自动化验证。\n"
            "- Rationale: 这些是普通排版标记。\n",
            encoding="utf-8",
        )
        code, out, err = QuietResult.run(
            scaffold_rules.main, ["validate", "--dir", str(self.test_dir)]
        )
        self.assertEqual(code, 0, out + err)

    def test_real_unfilled_placeholders_are_still_caught(self):
        """The relaxation must not let genuinely unfilled template slots through."""
        self._write_constitution(
            "# C\n\n## Overview\n1.0.0\n\n## Core Principles\n\n### P\n"
            "- 参见 [PROJECT_NAME] 与 [FEATURE_BRANCH]。\n"
        )
        code, _out, _err = QuietResult.run(
            scaffold_rules.main, ["validate", "--dir", str(self.test_dir)]
        )
        self.assertEqual(code, 1)

    # -- path containment --------------------------------------------------
    def test_constitution_path_cannot_escape_project_root(self):
        """Regression: --constitution-path accepted '..' and absolute paths."""
        outside = self.test_dir.parent / f"secret_{self.test_dir.name}.md"
        outside.write_text(
            "# Secret\n\n## Core Principles\n\n### 外部\n- EXFIL MUST NOT appear.\n",
            encoding="utf-8",
        )
        try:
            for label, path in [
                ("relative", "../" + outside.name),
                ("absolute", str(outside)),
            ]:
                with self.subTest(kind=label):
                    code, _out, err = QuietResult.run(
                        scaffold_rules.main,
                        ["inject", "--dir", str(self.test_dir), "--agents", "claude",
                         "--constitution-path", path],
                    )
                    self.assertEqual(code, 2)
                    self.assertIn("must stay inside the project root", err)
                    claude = self.test_dir / "CLAUDE.md"
                    self.assertFalse(claude.exists(), "wrote a file from an escaped path")
        finally:
            outside.unlink(missing_ok=True)

    # -- principle extraction ----------------------------------------------
    def test_level_two_section_principles_are_extracted(self):
        """Regression: '## I. Layering' style constitutions yielded zero principles."""
        body = (
            "# C\n\n## I. 分层隔离\n- 高层 MUST NOT 反向依赖底层实现。\n"
            "- 接口 MUST 显式声明。\n\n## II. 测试底线\n- 核心逻辑 MUST 有自动化测试。\n"
        )
        self._write_constitution(body)
        extracted = scaffold_rules.extract_principles(body)
        self.assertEqual(len(extracted), 2)

        code, _out, _err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude", "--strict"]
        )
        self.assertEqual(code, 0)
        claude = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("#### I. 分层隔离", claude)
        self.assertIn("高层 MUST NOT 反向依赖底层实现。", claude)
        self.assertNotIn("Refer to rules document", claude)

    def test_bullets_directly_under_core_principles_are_extracted(self):
        """Regression: bullets with no '###' sub-heading between them were dropped."""
        body = (
            "# C\n\n## Core Principles\n- 规则甲 MUST 成立。\n- 规则乙 MUST 成立。\n"
        )
        self._write_constitution(body)
        extracted = scaffold_rules.extract_principles(body)
        self.assertEqual(len(extracted), 1)
        self.assertEqual(extracted[0][0], "Core Principles")
        self.assertEqual(len(extracted[0][1]), 2)

    def test_loose_parse_does_not_over_grab_metadata(self):
        """The fallback must not promote an Overview section into a principle."""
        body = "# Empty Constitution\n\n## Overview\n\nNo principles here.\n"
        self.assertEqual(scaffold_rules.extract_principles(body), [])

    # -- injection behaviour -------------------------------------------------
    def test_repeated_agent_keys_inject_once(self):
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])
        code, out, _err = QuietResult.run(
            scaffold_rules.main,
            ["inject", "--dir", str(self.test_dir), "--agents", "claude,claude,CLAUDE"],
        )
        self.assertEqual(code, 0)
        written = out.count("[CREATED]") + out.count("[UPDATED]")
        self.assertEqual(written, 1)
        claude = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertEqual(claude.count(scaffold_rules.DEFAULT_START_MARKER), 1)

    def test_long_rule_truncation_is_announced(self):
        """Regression: rules over 200 chars were cut down silently."""
        self._write_constitution(
            "# C\n\n## Core Principles\n\n### 长规则\n- " + "X" * 260 + "\n"
        )
        _code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
        )
        self.assertIn("exceeds 200 characters", err)

    def test_unwritable_target_reports_exit_code_2(self):
        """Regression: a read-only context file raised a bare PermissionError."""
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])
        target = self.test_dir / "CLAUDE.md"
        target.write_text("# existing\n", encoding="utf-8")
        try:
            os.chmod(target, 0o444)
        except OSError as exc:  # pragma: no cover - platform dependent
            self.skipTest(f"cannot make file read-only here: {exc}")

        code, _out, err, exc = None, "", "", None
        try:
            code, _out, err = QuietResult.run(
                scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
            )
        except OSError as raised:  # pragma: no cover - the regression itself
            exc = raised

        self.assertIsNone(exc, "uncaughed OSError escaped the exit-code contract")
        self.assertEqual(code, 2)
        self.assertIn("Cannot write", err)

    # -- structural invariants ----------------------------------------------
    def test_signature_table_covers_every_agent_target(self):
        """A new target forgotten in AGENT_SIGNATURES would never be detected."""
        self.assertEqual(
            set(scaffold_rules.AGENT_SIGNATURES),
            set(scaffold_rules.AGENT_TARGET_MAP),
        )

    def test_init_reports_a_newly_created_directory(self):
        target = self.test_dir / "fresh" / "nested"
        code, out, _err = QuietResult.run(
            scaffold_rules.main, ["init", "--dir", str(target), "--name", "demo"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Target directory did not exist", out)


class TestUsabilityAndPreview(unittest.TestCase):
    """Usability findings: preview, honest verbs, language, actionable errors."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="proj_arch_test_"))
        scaffold_rules.main(["init", "--dir", str(self.test_dir), "--name", "demo", "--purpose", "p"])

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -- dry run -----------------------------------------------------------
    def test_dry_run_writes_nothing(self):
        """Regression: inject rewrote files with no way to preview the change."""
        code, out, _err = QuietResult.run(
            scaffold_rules.main,
            ["inject", "--dir", str(self.test_dir), "--agents", "claude,cursor", "--dry-run"],
        )
        self.assertEqual(code, 0)
        self.assertIn("[DRY-RUN]", out)
        self.assertFalse((self.test_dir / "CLAUDE.md").exists())
        self.assertFalse((self.test_dir / ".cursor").exists())

    def test_dry_run_reports_size_delta(self):
        (self.test_dir / "CLAUDE.md").write_text("# custom header\n", encoding="utf-8")
        code, out, _err = QuietResult.run(
            scaffold_rules.main,
            ["inject", "--dir", str(self.test_dir), "--agents", "claude", "--dry-run"],
        )
        self.assertEqual(code, 0)
        line = [l for l in out.splitlines() if "CLAUDE.md" in l and "bytes" in l]
        self.assertTrue(line, f"no size delta reported: {out}")
        self.assertIn("->", line[0])
        # Existing file is untouched, so the delta must be positive.
        self.assertIn("+", line[0])

    def test_dry_run_mentions_how_to_roll_back(self):
        _code, out, _err = QuietResult.run(
            scaffold_rules.main,
            ["inject", "--dir", str(self.test_dir), "--agents", "claude", "--dry-run"],
        )
        self.assertIn("Nothing was written", out)
        self.assertIn("roll back", out)

    def test_preview_and_write_share_one_code_path(self):
        """A preview that disagrees with the real run is worse than no preview."""
        previewed = self.test_dir / "previewed"
        direct = self.test_dir / "direct"
        for d in (previewed, direct):
            scaffold_rules.main(["init", "--dir", str(d), "--name", "demo", "--purpose", "p"])

        QuietResult.run(
            scaffold_rules.main,
            ["inject", "--dir", str(previewed), "--agents", "agents,claude,cursor", "--dry-run"],
        )
        scaffold_rules.main(["inject", "--dir", str(previewed), "--agents", "agents,claude,cursor"])
        scaffold_rules.main(["inject", "--dir", str(direct), "--agents", "agents,claude,cursor"])

        for rel in ["AGENTS.md", "CLAUDE.md", ".cursor/rules/project-rules.mdc"]:
            with self.subTest(file=rel):
                self.assertEqual(
                    (previewed / rel).read_bytes(),
                    (direct / rel).read_bytes(),
                )

    # -- honest verbs --------------------------------------------------------
    def test_created_and_updated_are_distinguished(self):
        """Regression: a re-run that updated an existing file still said INJECTED."""
        _code, first, _err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
        )
        _code, second, _err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
        )
        self.assertIn("[CREATED]", first)
        self.assertIn("[UPDATED]", second)
        self.assertNotIn("[CREATED]", second)

    # -- language ------------------------------------------------------------
    def test_summary_language_follows_the_constitution(self):
        const = self.test_dir / ".specify" / "memory" / "constitution.md"
        const.write_text(
            "# Constitution\n\n## Core Principles\n\n### Layering\n"
            "- Core logic MUST stay isolated from transports.\n",
            encoding="utf-8",
        )
        scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        claude = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("## Project Governance & Principles (Automated)", claude)
        self.assertNotIn("项目治理与核心原则", claude)

    def test_chinese_constitution_gets_chinese_labels(self):
        const = self.test_dir / ".specify" / "memory" / "constitution.md"
        const.write_text(
            "# 宪法\n\n## 核心原则\n\n### 分层隔离\n- 核心逻辑 MUST 与传输层解耦。\n",
            encoding="utf-8",
        )
        scaffold_rules.main(["inject", "--dir", str(self.test_dir), "--agents", "claude"])
        claude = (self.test_dir / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("## 项目治理与核心原则（自动生成）", claude)
        self.assertIn("### 工程卡点：", claude)
        self.assertNotIn("Engineering Checkpoints", claude)

    # -- error messages ------------------------------------------------------
    def test_directory_target_is_not_reported_as_permission_denied(self):
        """Windows reports opening a directory as [Errno 13], which misleads."""
        (self.test_dir / "CLAUDE.md").mkdir()
        code, _out, err = QuietResult.run(
            scaffold_rules.main, ["inject", "--dir", str(self.test_dir), "--agents", "claude"]
        )
        self.assertEqual(code, 2)
        self.assertIn("it is a directory", err)
        self.assertNotIn("Permission denied", err)

    # -- detect hands over the next step -------------------------------------
    def test_detect_shows_a_copyable_next_command(self):
        (self.test_dir / ".cursor").mkdir()
        code, out, _err = QuietResult.run(
            scaffold_rules.main, ["detect", "--dir", str(self.test_dir)]
        )
        self.assertEqual(code, 0)
        self.assertIn("scaffold_rules.py inject", out)
        self.assertIn("--strict", out)
        self.assertIn("--dry-run", out)

    # -- performance guard ----------------------------------------------------
    def test_target_dir_is_resolved_once_not_per_target(self):
        """On a network share every resolve() is several round-trips."""
        calls = {"n": 0}
        original = Path.resolve

        def counted(self, *a, **kw):
            calls["n"] += 1
            return original(self, *a, **kw)

        Path.resolve = counted
        try:
            scaffold_rules.main(
                ["inject", "--dir", str(self.test_dir), "--agents", ",".join(scaffold_rules.AGENT_TARGET_MAP)]
            )
        finally:
            Path.resolve = original
        # One resolve for the target root plus one containment check.
        self.assertLessEqual(calls["n"], 3, f"resolve() called {calls['n']} times")


if __name__ == "__main__":
    unittest.main()
