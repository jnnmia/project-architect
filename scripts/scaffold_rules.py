#!/usr/bin/env python3
"""Project Architect Scaffolder and Rule Injector.

Pure Python 3 standard library implementation for bootstrapping project rules,
managing the project constitution, and injecting rules into multi-agent context files.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DEFAULT_START_MARKER = "<!-- RULES START -->"
DEFAULT_END_MARKER = "<!-- RULES END -->"

AGENT_TARGET_MAP: dict[str, str] = {
    "agents": "AGENTS.md",
    "claude": "CLAUDE.md",
    "copilot": ".github/copilot-instructions.md",
    "gemini": "GEMINI.md",
    "cursor": ".cursor/rules/project-rules.mdc",
    "windsurf": ".windsurf/rules/project-rules.md",
    "trae": ".trae/rules/project_rules.md",
}


def _ensure_mdc_frontmatter(content: str) -> str:
    """Ensure .mdc file has alwaysApply: true in YAML frontmatter."""
    leading_ws = len(content) - len(content.lstrip())
    leading = content[:leading_ws]
    stripped = content[leading_ws:]

    if not stripped.startswith("---"):
        return "---\nalwaysApply: true\n---\n\n" + content

    match = re.match(
        r"^(---[ \t]*\r?\n)(.*?)(\r?\n---[ \t]*)(\r?\n|$)(.*)",
        stripped,
        re.DOTALL,
    )
    if not match:
        return "---\nalwaysApply: true\n---\n\n" + content

    opening, fm_text, closing, sep, rest = match.groups()
    newline = "\r\n" if "\r\n" in opening else "\n"

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*(?:#.*)?$", fm_text):
        return content

    if re.search(r"(?m)^[ \t]*alwaysApply[ \t]*:", fm_text):
        fm_text = re.sub(
            r"(?m)^([ \t]*)alwaysApply[ \t]*:.*?([ \t]*(?:#.*)?)$",
            r"\1alwaysApply: true\2",
            fm_text,
            count=1,
        )
    elif fm_text.strip():
        fm_text = fm_text + newline + "alwaysApply: true"
    else:
        fm_text = "alwaysApply: true"

    return f"{leading}{opening}{fm_text}{closing}{sep}{rest}"


def _upsert_marker_section(
    file_path: Path,
    start_marker: str,
    end_marker: str,
    section_content: str,
    is_mdc: bool = False,
) -> None:
    """Insert or replace the content between markers with single-sided recovery."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    block = f"{start_marker}\n{section_content.strip()}\n{end_marker}\n"

    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        s = content.find(start_marker)
        e = content.find(end_marker, s if s != -1 else 0)

        # Case 1: Both markers present in correct sequence
        if s != -1 and e != -1 and e > s:
            end_pos = e + len(end_marker)
            if end_pos < len(content) and content[end_pos] == "\r":
                end_pos += 1
            if end_pos < len(content) and content[end_pos] == "\n":
                end_pos += 1
            new_content = content[:s] + block + content[end_pos:]
        # Case 2: Only start marker exists (corrupted/half-edited) -> replace from start marker to end
        elif s != -1:
            new_content = content[:s] + block
        # Case 3: Only end marker exists (corrupted/half-edited) -> replace up to end marker
        elif e != -1:
            end_pos = e + len(end_marker)
            if end_pos < len(content) and content[end_pos] == "\r":
                end_pos += 1
            if end_pos < len(content) and content[end_pos] == "\n":
                end_pos += 1
            new_content = block + content[end_pos:]
        # Case 4: Neither marker exists -> append to file
        else:
            sep = "\n\n" if content and not content.endswith("\n\n") else ("\n" if content and not content.endswith("\n") else "")
            new_content = content + sep + block
    else:
        new_content = block

    new_content = new_content.replace("\r\n", "\n")
    if is_mdc:
        new_content = _ensure_mdc_frontmatter(new_content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)


def _load_asset_template(template_name: str) -> str:
    """Load template from skill asset directory."""
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "assets" / "templates" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize project constitution and specification templates."""
    target_dir = Path(args.dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    project_name = args.name or target_dir.name
    purpose = args.purpose or "工程化软件项目"

    mem_dir = target_dir / ".specify" / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    constitution_file = mem_dir / "constitution.md"

    if constitution_file.exists() and not args.force:
        print(f"[SKIP] Constitution file already exists: {constitution_file}")
    else:
        template = _load_asset_template("constitution-template.md")
        rendered = template.replace("[PROJECT_NAME]", project_name)
        rendered = rendered.replace("[PROJECT_PURPOSE_SUMMARY]", purpose)
        with open(constitution_file, "w", encoding="utf-8") as f:
            f.write(rendered)
        print(f"[CREATED] Constitution initialized at: {constitution_file}")

    templates_dir = target_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    for tmpl in ["plan-template.md", "spec-template.md", "tasks-template.md"]:
        out_path = templates_dir / tmpl
        if out_path.exists() and not args.force:
            print(f"[SKIP] Template already exists: {out_path}")
        else:
            content = _load_asset_template(tmpl)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[CREATED] Template copied to: {out_path}")

    # Ensure baseline AGENTS.md exists
    agents_file = target_dir / "AGENTS.md"
    if not agents_file.exists():
        baseline_agents = (
            f"# {project_name} - Agent Governance\n\n"
            "> 项目核心工程规范与底线规则定义于 [.specify/memory/constitution.md](./.specify/memory/constitution.md)。\n"
        )
        with open(agents_file, "w", encoding="utf-8") as f:
            f.write(baseline_agents)
        print(f"[CREATED] Baseline AGENTS.md created at: {agents_file}")

    print("\n[SUCCESS] Project rule scaffolding complete.")
    return 0


PRINCIPLES_SECTION_PATTERN = re.compile(
    r"^##\s+.*(?:core\s+principles?|principles?|核心原则|核心规范|底线规则|ground\s+rules)",
    re.IGNORECASE,
)
METADATA_SECTION_PATTERN = re.compile(
    r"^##\s+.*(?:overview|workflow|checkpoint|impact\s+report|template|概览|简介|流程|卡点|模板|目录)",
    re.IGNORECASE,
)
RATIONALE_LINE_PATTERN = re.compile(
    r"^[*_~`#\s]*(?:rationale|说明|原因|背景)\b",
    re.IGNORECASE,
)


def extract_principles(content: str) -> list[tuple[str, list[str]]]:
    """Extract principles and their normative rules from markdown constitution content.

    Resiliently handles:
    - Roman numerals (I., II., VI., X., etc.)
    - Arabic numerals (1., 2., etc.)
    - Chinese numerals (原则一, 一、, etc.)
    - Plain titles without numbers
    - Scoped extraction to '## Core Principles' section if present
    - Filtering out rationales and non-principle metadata sections
    """
    lines = content.splitlines()

    # 1. Determine principle section scope
    start_idx = 0
    end_idx = len(lines)
    has_principles_header = False

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if PRINCIPLES_SECTION_PATTERN.match(line):
            start_idx = i + 1
            has_principles_header = True
            break

    if has_principles_header:
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            # Stop at the next major section (level 1 or 2 heading)
            if re.match(r"^#{1,2}\s+", line) and not line.startswith("###"):
                end_idx = i
                break
        scoped_lines = lines[start_idx:end_idx]
    else:
        # If no explicit Principles section header, use lines excluding known metadata sections
        scoped_lines = []
        in_metadata_section = False
        for raw_line in lines:
            line = raw_line.strip()
            if METADATA_SECTION_PATTERN.match(line):
                in_metadata_section = True
            elif line.startswith("## "):
                in_metadata_section = False

            if not in_metadata_section:
                scoped_lines.append(raw_line)

    # 2. Extract subsections and rules
    principles_data: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_rules: list[str] = []

    for raw_line in scoped_lines:
        line = raw_line.strip()
        # Detect principle heading (level 3 or level 4 heading)
        header_match = re.match(r"^(?:###|####)\s+(.+)$", line)
        if header_match:
            title_candidate = header_match.group(1).strip()
            if RATIONALE_LINE_PATTERN.match(title_candidate) or re.match(r"^(?:overview|workflow|checkpoint|概览|流程|卡点)", title_candidate, re.IGNORECASE):
                continue

            if current_title:
                principles_data.append((current_title, current_rules))
            current_title = title_candidate
            current_rules = []
            continue

        # Detect bullet rule under current principle
        if current_title:
            bullet_match = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", line)
            if bullet_match:
                rule_text = bullet_match.group(1).strip()
                if RATIONALE_LINE_PATTERN.match(rule_text):
                    continue
                if len(rule_text) > 200:
                    rule_text = rule_text[:197] + "..."
                current_rules.append(rule_text)

    if current_title:
        principles_data.append((current_title, current_rules))

    return principles_data


def cmd_inject(args: argparse.Namespace) -> int:
    """Inject constitution summary into specified agent context files."""
    target_dir = Path(args.dir).resolve()
    const_file = target_dir / args.constitution_path

    if not const_file.exists():
        print(f"[ERROR] Constitution file not found: {const_file}", file=sys.stderr)
        return 1

    with open(const_file, "r", encoding="utf-8") as f:
        content = f.read()

    principles_data = extract_principles(content)

    summary_lines = [
        "## Project Governance & Principles (Automated)",
        f"Rules Source of Truth: `{args.constitution_path}`",
        "",
        "### Core Architectural & Quality Invariants:",
    ]

    if principles_data:
        for title, rules in principles_data:
            summary_lines.append(f"#### {title}")
            for r in rules:
                summary_lines.append(f"- {r}")
            if not rules:
                summary_lines.append("- (Refer to constitution for detailed rules)")
    else:
        warn_msg = f"[WARN] No principles extracted from {const_file}. Ensure principles are defined under '## Core Principles' with '### <Title>' headers."
        print(warn_msg, file=sys.stderr)
        if getattr(args, "strict", False):
            print(f"[FAIL] Injection aborted due to --strict flag: 0 principles extracted.", file=sys.stderr)
            return 1
        summary_lines.append("- Refer to rules document for binding MUST/SHOULD principles.")

    summary_lines.extend([
        "",
        "### Engineering Checkpoints:",
        "1. Verify proposed plans against core project rules.",
        "2. Maintain automated test coverage for critical business logic.",
        "3. Keep rule updates within boundary markers without overwriting custom configurations.",
    ])

    summary_content = "\n".join(summary_lines)

    selected_agents = [a.strip().lower() for a in args.agents.split(",") if a.strip()]
    injected_count = 0

    for agent in selected_agents:
        if agent not in AGENT_TARGET_MAP:
            print(f"[WARN] Unknown agent key: '{agent}'. Supported: {', '.join(AGENT_TARGET_MAP.keys())}")
            continue

        rel_path = AGENT_TARGET_MAP[agent]
        dest_file = target_dir / rel_path
        is_mdc = rel_path.endswith(".mdc")

        _upsert_marker_section(
            dest_file,
            DEFAULT_START_MARKER,
            DEFAULT_END_MARKER,
            summary_content,
            is_mdc=is_mdc,
        )
        print(f"[INJECTED] Updated agent context: {dest_file}")
        injected_count += 1

    print(f"\n[SUCCESS] Successfully injected rules into {injected_count} agent file(s).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate constitution file against governance standards."""
    target_dir = Path(args.dir).resolve()
    const_file = target_dir / args.constitution_path

    if not const_file.exists():
        print(f"[FAIL] Constitution file does not exist: {const_file}")
        return 1

    with open(const_file, "r", encoding="utf-8") as f:
        text = f.read()

    errors: list[str] = []

    # 1. Check placeholders
    placeholders = re.findall(r"\[[A-Z0-9_]{3,}\]", text)
    if placeholders:
        errors.append(f"Unresolved placeholders found: {', '.join(set(placeholders))}")

    # 2. Check RFC 2119 keywords
    if "MUST" not in text:
        errors.append("Constitution lacks declarative 'MUST' normative constraints.")

    # 3. Check Rationale
    if "Rationale" not in text and "*Rationale:*" not in text:
        errors.append("Principles should include architectural 'Rationale' justifications.")

    # 4. Check SemVer or Version change
    if (
        "Version change:" not in text
        and "SemVer" not in text
        and "1.0.0" not in text
        and "v1." not in text
        and "0.0.1" not in text
        and "v0." not in text
    ):
        errors.append("Constitution lacks explicit versioning indicator or Sync Impact Report.")

    if errors:
        print("[FAIL] Constitution validation errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[PASS] Constitution '{const_file}' meets all governance criteria.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scaffold_rules.py",
        description="Project Architect: Scaffold rules and manage multi-agent context injection.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Init
    p_init = subparsers.add_parser("init", help="Initialize project constitution and templates")
    p_init.add_argument("--dir", default=".", help="Target project root directory")
    p_init.add_argument("--name", default="", help="Project name")
    p_init.add_argument("--purpose", default="", help="Project purpose description")
    p_init.add_argument("--force", action="store_true", help="Force overwrite existing files")

    # Inject
    p_inject = subparsers.add_parser("inject", help="Inject rules into agent context files")
    p_inject.add_argument("--dir", default=".", help="Target project root directory")
    p_inject.add_argument(
        "--agents",
        default="agents,claude,cursor",
        help="Comma-separated agent keys (agents,claude,copilot,gemini,cursor,windsurf,trae)",
    )
    p_inject.add_argument(
        "--constitution-path",
        default=".specify/memory/constitution.md",
        help="Project-relative path to constitution file",
    )
    p_inject.add_argument(
        "--strict",
        action="store_true",
        help="Fail with exit code 1 if zero principles are extracted from constitution",
    )

    # Validate
    p_val = subparsers.add_parser("validate", help="Validate constitution file quality")
    p_val.add_argument("--dir", default=".", help="Target project root directory")
    p_val.add_argument(
        "--constitution-path",
        default=".specify/memory/constitution.md",
        help="Project-relative path to constitution file",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "init":
        return cmd_init(args)
    elif args.subcommand == "inject":
        return cmd_inject(args)
    elif args.subcommand == "validate":
        return cmd_validate(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
