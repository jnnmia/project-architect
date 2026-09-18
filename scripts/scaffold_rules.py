#!/usr/bin/env python3
"""Project Architect Scaffolder and Rule Injector.

Pure Python 3 standard library implementation for bootstrapping project rules,
managing the project constitution, and injecting rules into multi-agent context files.

Exit codes:
    0  Success.
    1  Rule-level failure: validation errors, no principles extracted under
       --strict, an agent key / target that could not be honoured, or `detect`
       finding no tool signature at all.
    2  I/O failure: unreadable or unwritable file, missing asset template, a
       file that is not valid UTF-8, or a --constitution-path that escapes the
       project root.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_START_MARKER = "<!-- RULES START -->"
DEFAULT_END_MARKER = "<!-- RULES END -->"


class RuleIOError(Exception):
    """Raised when a context file cannot be read or written as UTF-8 text."""


def normalise_newlines(text: str) -> str:
    """Collapse CRLF and lone CR into LF so output is platform-independent."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def read_text(source: Path | str) -> str:
    """Read a file as UTF-8 text, stripping any BOM, with LF-only newlines.

    Decoding is strict: a file that is not valid UTF-8 (for example a
    CP936-encoded file saved by a legacy Windows editor) raises RuleIOError
    instead of a bare UnicodeDecodeError traceback.
    """
    path = Path(source)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        # Windows reports opening a directory as [Errno 13] Permission denied,
        # which sends people hunting for ACLs instead of noticing the typo.
        if isinstance(exc, IsADirectoryError) or path.is_dir():
            raise RuleIOError(f"Cannot read {path}: it is a directory, not a file.") from None
        raise RuleIOError(f"Cannot read {path}: {exc}") from exc

    try:
        # utf-8-sig transparently drops a leading BOM and is a no-op without one.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuleIOError(
            f"{path} is not valid UTF-8 (offending byte at offset {exc.start}). "
            "Re-save the file as UTF-8 and retry."
        ) from exc

    return normalise_newlines(text)


def write_text(destination: Path, text: str) -> None:
    """Write UTF-8 text with explicit LF newlines, never platform-native ones.

    Passing newline="\\n" is what keeps Windows output byte-identical to Linux
    output; without it Python rewrites every \\n as \\r\\n on Windows.
    """
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8", newline="\n") as f:
            f.write(normalise_newlines(text))
    except OSError as exc:
        # Read-only files, full disks and permissions must surface as a clean
        # error code, not an OSError traceback past the exit-code contract.
        if isinstance(exc, IsADirectoryError) or destination.is_dir():
            raise RuleIOError(f"Cannot write {destination}: it is a directory.") from exc
        raise RuleIOError(f"Cannot write {destination}: {exc}") from exc


def resolve_within(root: Path, relative: str, flag: str) -> Path:
    """Resolve a project-relative path, refusing anything that escapes root.

    `root` must already be resolved by the caller: on a network share every
    resolve() costs several round-trips, and re-resolving a path we just
    resolved is pure waste.

    The reference documentation promises that targets stay inside the project
    root; pathlib does not enforce that on its own. Joining with `/` silently
    replaces the base when given an absolute path, and '..' climbs out
    unchallenged, both of which let a caller pull outside content into an
    injected rule summary.
    """
    candidate = Path(relative)

    if candidate.is_absolute():
        raise RuleIOError(
            f"{flag} must stay inside the project root ({root}), "
            f"but '{relative}' is an absolute path."
        )

    parts = [p for p in candidate.parts if p not in ("", ".")]
    if ".." in parts:
        raise RuleIOError(
            f"{flag} must stay inside the project root ({root}), "
            f"but '{relative}' climbs out of it."
        )

    resolved = (root / Path(*parts)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise RuleIOError(
            f"{flag} resolves to {resolved}, outside the project root {root}."
        ) from None
    return resolved


AGENT_TARGET_MAP: dict[str, str] = {
    "agents": "AGENTS.md",
    "claude": "CLAUDE.md",
    "copilot": ".github/copilot-instructions.md",
    "gemini": "GEMINI.md",
    "cursor": ".cursor/rules/project-rules.mdc",
    "windsurf": ".windsurf/rules/project-rules.md",
    "trae": ".trae/rules/project_rules.md",
    "cline": ".clinerules",
    "continue": ".continue/prompts/project-rules.md",
}

# On-disk evidence that a project actually uses a given tool. Used only by
# `detect`, which never writes anything: the scan is evidence to drive a
# question to the user, never a substitute for their consent. Most specific
# signatures come first so the reported evidence is the most telling one.
AGENT_SIGNATURES: dict[str, tuple[str, ...]] = {
    "agents": ("AGENTS.md",),
    "claude": ("CLAUDE.md", ".claude"),
    "copilot": (".github/copilot-instructions.md",),
    "gemini": ("GEMINI.md", ".gemini"),
    "cursor": (".cursor/rules/project-rules.mdc", ".cursor/rules", ".cursor", ".cursorrules"),
    "windsurf": (".windsurf",),
    "trae": (".trae",),
    "cline": (".clinerules", ".cline"),
    "continue": (".continue",),
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


def _plan_marker_section(
    file_path: Path,
    start_marker: str,
    end_marker: str,
    section_content: str,
    is_mdc: bool = False,
) -> tuple[str, str]:
    """Compute (action, new_content) without touching the filesystem.

    Splitting the plan from the write is what makes --dry-run honest: the
    preview and the real write run through the exact same code path, so a
    preview cannot disagree with what would have happened.

    Returns action = "create" when the file does not exist yet, "update"
    otherwise.
    """
    block = f"{start_marker}\n{section_content.strip()}\n{end_marker}\n"
    action = "update"

    if file_path.exists():
        content = read_text(file_path)

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
        action = "create"

    if is_mdc:
        new_content = _ensure_mdc_frontmatter(new_content)

    return action, new_content


def _upsert_marker_section(
    file_path: Path,
    start_marker: str,
    end_marker: str,
    section_content: str,
    is_mdc: bool = False,
) -> str:
    """Insert or replace the content between markers. Returns the action taken."""
    action, new_content = _plan_marker_section(
        file_path, start_marker, end_marker, section_content, is_mdc
    )
    write_text(file_path, new_content)
    return action


def _plan_eject_marker_section(
    file_path: Path,
    start_marker: str,
    end_marker: str,
    is_mdc: bool = False,
) -> tuple[str, str, bool]:
    """Compute (action, new_content, should_delete) for ejecting a marker block.

    Returns:
        action: "delete" (if only generated rules/frontmatter remain),
                "update" (if user custom content remains outside markers),
                "skip" (if file does not exist or markers not found)
        new_content: cleaned file content
        should_delete: boolean indicating whether file should be unlinked
    """
    if not file_path.is_file():
        return "skip", "", False

    content = read_text(file_path)
    s = content.find(start_marker)
    e = content.find(end_marker, s if s != -1 else 0)

    if s == -1 or e == -1 or e <= s:
        return "skip", content, False

    end_pos = e + len(end_marker)
    if end_pos < len(content) and content[end_pos] == "\r":
        end_pos += 1
    if end_pos < len(content) and content[end_pos] == "\n":
        end_pos += 1

    before = content[:s].rstrip()
    after = content[end_pos:].lstrip()

    if before and after:
        new_content = before + "\n\n" + after
    elif before:
        new_content = before + "\n"
    elif after:
        new_content = after
    else:
        new_content = ""

    stripped_residual = new_content.strip()

    # For .mdc files, check if remaining content is only the default frontmatter
    if is_mdc:
        fm_match = re.match(
            r"^---[ \t]*\r?\n[ \t]*alwaysApply[ \t]*:[ \t]*true[ \t]*(?:#.*)?\r?\n---[ \t]*$",
            stripped_residual,
        )
        if fm_match or not stripped_residual:
            return "delete", "", True

    if not stripped_residual:
        return "delete", "", True

    return "update", new_content, False



def _load_asset_template(template_name: str) -> str:
    """Load a template from the sibling assets/templates directory.

    Templates are resolved relative to this script, which works for every
    supported layout: the development checkout, an `npx skills` install, and a
    skillhub install (e.g. skills/project-architect__skillhub). A source tree
    that is missing assets/ is reported with actionable guidance rather than a
    bare FileNotFoundError.
    """
    script_dir = Path(__file__).resolve().parent
    template_path = script_dir.parent / "assets" / "templates" / template_name
    if not template_path.is_file():
        raise RuleIOError(
            f"Template not found: {template_path}. "
            "This tool must run from a skill directory that contains both "
            "'scripts/' and 'assets/templates/'. If the skill was copied "
            "partially, re-install it with 'npx skills add jnnmia/project-architect'."
        )
    return read_text(template_path)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize project constitution and specification templates."""
    target_dir = Path(args.dir).resolve()
    # A typo in --dir would otherwise scaffold into a brand new directory tree
    # without saying anything. Creating the target is legitimate; doing it
    # silently is not, so the action is always reported.
    created_root = not target_dir.is_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    if created_root:
        print(f"[NOTICE] Target directory did not exist; created: {target_dir}")

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
        write_text(constitution_file, rendered)
        print(f"[CREATED] Constitution initialized at: {constitution_file}")

    templates_dir = target_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)

    for tmpl in ["plan-template.md", "spec-template.md", "tasks-template.md"]:
        out_path = templates_dir / tmpl
        if out_path.exists() and not args.force:
            print(f"[SKIP] Template already exists: {out_path}")
        else:
            content = _load_asset_template(tmpl)
            write_text(out_path, content)
            print(f"[CREATED] Template copied to: {out_path}")

    # Ensure baseline AGENTS.md exists
    agents_file = target_dir / "AGENTS.md"
    if not agents_file.exists():
        baseline_agents = (
            f"# {project_name} - Agent Governance\n\n"
            "> 项目核心工程规范与底线规则定义于 [.specify/memory/constitution.md](./.specify/memory/constitution.md)。\n"
        )
        write_text(agents_file, baseline_agents)
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


def extract_principles(content: str, max_rule_len: int = 200) -> list[tuple[str, list[str]]]:
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
                if max_rule_len > 0 and len(rule_text) > max_rule_len:
                    truncated_at = current_title or "untitled"
                    print(
                        f"[WARN] A rule under '{truncated_at}' exceeds {max_rule_len} characters and "
                        "was truncated. Keep summary rules short; leave the detail in "
                        "the constitution itself.",
                        file=sys.stderr,
                    )
                    rule_text = rule_text[: max_rule_len - 3] + "..."
                current_rules.append(rule_text)

    if current_title:
        principles_data.append((current_title, current_rules))

    if not principles_data:
        principles_data = _extract_principles_loose(lines, max_rule_len=max_rule_len)

    return principles_data



def _extract_principles_loose(lines: list[str], max_rule_len: int = 200) -> list[tuple[str, list[str]]]:
    """Fallback pass for two authoring styles the strict parser cannot see.

    The strict parser requires '### <Title>' subsections. Real constitutions
    are also written as:

        ## Core Principles
        - Rule one MUST hold.

    (bullets sitting directly under the principles heading), or as

        ## I. Layering
        - ...
        ## II. Tests
        - ...

    (whole sections at level 2). Both used to yield zero principles, which in
    turn produced a stub rule summary instead of the actual rules. Level 2
    headings are used as the group titles; metadata sections are skipped, and
    groups without a single rule are dropped.
    """
    principles: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_rules: list[str] = []

    for raw_line in lines:
        line = raw_line.strip()

        header_match = re.match(r"^##\s+(.+)$", line)
        if header_match:
            title_candidate = header_match.group(1).strip()
            if current_title is not None and current_rules:
                principles.append((current_title, current_rules))
            current_title = title_candidate
            current_rules = []
            if METADATA_SECTION_PATTERN.match(line) or RATIONALE_LINE_PATTERN.match(title_candidate):
                current_title = None
            continue

        if current_title is not None:
            bullet_match = re.match(r"^(?:[-*+]|\d+\.)\s+(.+)$", line)
            if bullet_match and not RATIONALE_LINE_PATTERN.match(bullet_match.group(1)):
                rule_text = bullet_match.group(1).strip()
                if max_rule_len > 0 and len(rule_text) > max_rule_len:
                    truncated_at = current_title or "untitled"
                    print(
                        f"[WARN] A rule under '{truncated_at}' exceeds {max_rule_len} characters and "
                        "was truncated. Keep summary rules short; leave the detail in "
                        "the constitution itself.",
                        file=sys.stderr,
                    )
                    rule_text = rule_text[: max_rule_len - 3] + "..."
                current_rules.append(rule_text)

    if current_title is not None and current_rules:
        principles.append((current_title, current_rules))

    # The document title and any heading already consumed are not principles.
    return [(title, rules) for title, rules in principles if rules]



def detect_agent_signatures(target_dir: Path) -> dict[str, list[str]]:
    """Return {agent_key: [existing signature paths]} for the target project.

    Read-only by design. An empty result is a normal outcome, not a failure:
    a brand-new project carries no signatures at all, which is precisely when
    the caller must ask the user instead of guessing.
    """
    detected: dict[str, list[str]] = {}
    for agent, signatures in AGENT_SIGNATURES.items():
        hits = [sig for sig in signatures if (target_dir / sig).exists()]
        if hits:
            detected[agent] = hits
    return detected


def cmd_detect(args: argparse.Namespace) -> int:
    """Report which AI tools a project shows evidence of using. Writes nothing."""
    target_dir = Path(args.dir).resolve()
    if not target_dir.is_dir():
        print(f"[ERROR] Target directory does not exist: {target_dir}", file=sys.stderr)
        return 2

    detected = detect_agent_signatures(target_dir)

    print(f"Scanning {target_dir} for AI tool signatures\n")
    for agent in AGENT_TARGET_MAP:
        hits = detected.get(agent)
        if hits:
            print(f"  [FOUND]     {agent:<9} <- {', '.join(hits)}")
        else:
            print(f"  [no trace]  {agent:<9} (nothing on disk)")

    if not detected:
        # Not a failure of the tool: a brand-new project legitimately has no
        # traces. Calling it [FAIL] told people something was broken when the
        # only correct action is to go and ask.
        print(
            "\n[NOTICE] No supported AI tool signature found. This project is either "
            "brand new or uses tools this skill does not know about.\n"
            "         Nothing here to base a decision on - ask the user which tools "
            "they use, and do NOT inject into everything.",
            file=sys.stderr,
        )
        return 1 if getattr(args, "fail_if_empty", False) else 0


    print(
        f"\n[SUCCESS] Found traces of {len(detected)} tool(s): {', '.join(detected)}"
    )
    print(
        "Evidence only, not consent: confirm with the user which of these they actually\n"
        "use before injecting, and never add a tool they did not mention."
    )

    # Hand the next command over instead of making people reconstruct it from
    # the README. --agents still has to be edited down to the confirmed subset;
    # that edit is the whole point of the confirm step.
    print("\nNext step, once the user has confirmed the subset:")
    print(f"  python scripts/scaffold_rules.py inject \\")
    print(f"    --dir \"{target_dir}\" --agents \"{','.join(detected)}\" --strict")
    print(
        "  Add --dry-run first to preview the change without writing anything."
    )
    return 0


SUMMARY_LABELS: dict[str, dict[str, object]] = {
    "en": {
        "heading": "## Project Governance & Principles (Automated)",
        "source": "Rules Source of Truth:",
        "invariants": "### Core Architectural & Quality Invariants:",
        "empty_rule": "- (Refer to constitution for detailed rules)",
        "fallback": "- Refer to rules document for binding MUST/SHOULD principles.",
        "checkpoints": "### Engineering Checkpoints:",
        "checkpoint_items": [
            "1. Verify proposed plans against core project rules.",
            "2. Maintain automated test coverage for critical business logic.",
            "3. Keep rule updates within boundary markers without overwriting custom configurations.",
        ],
    },
    "zh": {
        "heading": "## 项目治理与核心原则（自动生成）",
        "source": "规则事实源：",
        "invariants": "### 核心架构与质量不变量：",
        "empty_rule": "- （详细规则见宪法原文）",
        "fallback": "- 绑定性 MUST / SHOULD 原则见规则文档。",
        "checkpoints": "### 工程卡点：",
        "checkpoint_items": [
            "1. 方案推进前 MUST 对照项目核心规则自检。",
            "2. 核心业务逻辑 MUST 保持自动化测试覆盖。",
            "3. 规则更新 MUST 只落在边界标记内，不得覆盖自定义配置。",
        ],
    },
}


def contains_cjk(text: str) -> bool:
    return any("一" <= ch <= "鿿" for ch in text)


def summary_language(principles_data: list[tuple[str, list[str]]], content: str) -> str:
    """Match the generated block's language to the constitution's language.

    The rules themselves come from the user's constitution and are copied
    verbatim; only the surrounding labels are ours. Hardcoding English labels
    left a Chinese project with an English-framed block inside its own
    Chinese rules file.
    """
    if principles_data:
        sample = " ".join(title + " " + " ".join(rules) for title, rules in principles_data)
    else:
        sample = content
    return "zh" if contains_cjk(sample) else "en"


def cmd_inject(args: argparse.Namespace) -> int:
    """Inject constitution summary into specified agent context files."""
    target_dir = Path(args.dir).resolve()
    const_file = resolve_within(target_dir, args.constitution_path, "--constitution-path")

    if not const_file.exists():
        print(f"[ERROR] Constitution file not found: {const_file}", file=sys.stderr)
        return 1

    content = read_text(const_file)
    max_rule_len = getattr(args, "max_rule_len", 200)
    principles_data = extract_principles(content, max_rule_len=max_rule_len)


    labels = SUMMARY_LABELS[summary_language(principles_data, content)]

    summary_lines = [
        str(labels["heading"]),
        f"{labels['source']} `{args.constitution_path}`",
        "",
        str(labels["invariants"]),
    ]

    if principles_data:
        for title, rules in principles_data:
            summary_lines.append(f"#### {title}")
            for r in rules:
                summary_lines.append(f"- {r}")
            if not rules:
                summary_lines.append(str(labels["empty_rule"]))
    else:
        warn_msg = f"[WARN] No principles extracted from {const_file}. Ensure principles are defined under '## Core Principles' with '### <Title>' headers."
        print(warn_msg, file=sys.stderr)
        if getattr(args, "strict", False):
            print(f"[FAIL] Injection aborted due to --strict flag: 0 principles extracted.", file=sys.stderr)
            return 1
        summary_lines.append(str(labels["fallback"]))

    summary_lines.extend(["", str(labels["checkpoints"])])
    summary_lines.extend(str(item) for item in labels["checkpoint_items"])  # type: ignore[union-attr]

    summary_content = "\n".join(summary_lines)

    raw_keys = [a.strip().lower() for a in args.agents.split(",") if a.strip()]
    # 'claude,CLAUDE' written twice must not double-inject or inflate the count.
    selected_agents = list(dict.fromkeys(raw_keys))
    unknown_agents = [a for a in selected_agents if a not in AGENT_TARGET_MAP]
    injected_count = 0

    for agent in selected_agents:
        if agent not in AGENT_TARGET_MAP:
            continue

        rel_path = AGENT_TARGET_MAP[agent]
        dest_file = target_dir / rel_path
        is_mdc = rel_path.endswith(".mdc")

        if getattr(args, "dry_run", False):
            action, planned = _plan_marker_section(
                dest_file,
                DEFAULT_START_MARKER,
                DEFAULT_END_MARKER,
                summary_content,
                is_mdc,
            )
            before = dest_file.stat().st_size if dest_file.is_file() else 0
            after = len(planned.encode("utf-8"))
            print(
                f"[DRY-RUN] would {action} {dest_file} "
                f"({before} -> {after} bytes, {after - before:+d})"
            )
        else:
            action = _upsert_marker_section(
                dest_file,
                DEFAULT_START_MARKER,
                DEFAULT_END_MARKER,
                summary_content,
                is_mdc,
            )
            print(f"[{'CREATED' if action == 'create' else 'UPDATED'}] agent context: {dest_file}")
        injected_count += 1

    # A misspelled target used to be reported as a warning while the command
    # still exited 0, so typos silently produced a partially-configured
    # project. Any rejected key is an error signal to the caller.
    for agent in unknown_agents:
        print(
            f"[ERROR] Unknown agent key: '{agent}'. "
            f"Supported: {', '.join(AGENT_TARGET_MAP)}",
            file=sys.stderr,
        )

    if injected_count == 0:
        print("[ERROR] No agent context file was updated.", file=sys.stderr)
        return 1

    if unknown_agents:
        print(
            f"\n[FAIL] Injected rules into {injected_count} agent file(s), "
            f"but {len(unknown_agents)} agent key(s) were rejected.",
            file=sys.stderr,
        )
        return 1

    if getattr(args, "dry_run", False):
        # Saying "Successfully injected" while nothing was written is a lie the
        # user has to read three more lines to discover.
        print(
            f"\n[SUCCESS] Preview complete: {injected_count} agent file(s) would be affected."
            "\n[DRY-RUN] Nothing was written. Re-run without --dry-run to apply.\n"
            "          To roll back an applied change, delete the block between\n"
            f"          {DEFAULT_START_MARKER} and {DEFAULT_END_MARKER}."
        )
    else:
        print(f"\n[SUCCESS] Successfully injected rules into {injected_count} agent file(s).")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate constitution file against governance standards."""
    target_dir = Path(args.dir).resolve()
    const_file = resolve_within(target_dir, args.constitution_path, "--constitution-path")

    if not const_file.exists():
        print(f"[FAIL] Constitution file does not exist: {const_file}")
        return 1

    text = read_text(const_file)

    errors: list[str] = []

    # 1. Check placeholders. Only template-shaped tokens count: a bare
    # bracketed word such as [TODO] or [NOTE] is ordinary prose, not an
    # unfilled slot left behind by a template.
    tokens = re.findall(r"\[([A-Z0-9_]{3,})\]", text)
    unresolved = [t for t in tokens if "_" in t and len(t) >= 6]
    if unresolved:
        # dict.fromkeys keeps first-occurrence order, so this message is
        # byte-identical across runs. Iterating a set would reshuffle it by
        # PYTHONHASHSEED and break the determinism guarantee.
        errors.append(
            "Unresolved placeholders found: "
            + ", ".join(f"[{t}]" for t in dict.fromkeys(unresolved))
        )

    # 2. Check RFC 2119 keywords or Chinese normative keywords
    has_normative = bool(re.search(r"\bMUST\b", text)) or bool(re.search(r"(?:必须|严禁|不得|禁止)", text))
    if not has_normative:
        errors.append("Constitution lacks declarative 'MUST' or Chinese normative constraints (必须/严禁/不得/禁止).")

    # 3. Check Rationale
    has_rationale = (
        "Rationale" in text
        or "*Rationale:*" in text
        or bool(re.search(r"(?:架构理由|选型理由|设计理由|设计说明)\b", text))
    )
    if not has_rationale:
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


def cmd_eject(args: argparse.Namespace) -> int:
    """Eject injected rules from agent context files."""
    target_dir = Path(args.dir).resolve()
    if not target_dir.is_dir():
        print(f"[ERROR] Target directory does not exist: {target_dir}", file=sys.stderr)
        return 2

    raw_keys = [a.strip().lower() for a in args.agents.split(",") if a.strip()]
    selected_agents = list(dict.fromkeys(raw_keys))
    unknown_agents = [a for a in selected_agents if a not in AGENT_TARGET_MAP]

    ejected_count = 0
    for agent in selected_agents:
        if agent not in AGENT_TARGET_MAP:
            continue

        rel_path = AGENT_TARGET_MAP[agent]
        dest_file = target_dir / rel_path
        is_mdc = rel_path.endswith(".mdc")

        if not dest_file.exists():
            print(f"[SKIP] target file does not exist: {dest_file}")
            continue

        action, cleaned_content, should_delete = _plan_eject_marker_section(
            dest_file,
            DEFAULT_START_MARKER,
            DEFAULT_END_MARKER,
            is_mdc,
        )

        if action == "skip":
            print(f"[SKIP] no rules markers found in: {dest_file}")
            continue

        if getattr(args, "dry_run", False):
            if should_delete:
                print(f"[DRY-RUN] would delete {dest_file} (no user content remains)")
            else:
                before_size = dest_file.stat().st_size
                after_size = len(cleaned_content.encode("utf-8"))
                print(
                    f"[DRY-RUN] would update {dest_file} "
                    f"({before_size} -> {after_size} bytes, {after_size - before_size:+d})"
                )
        else:
            if should_delete:
                dest_file.unlink(missing_ok=True)
                print(f"[DELETED] empty agent context: {dest_file}")
                try:
                    dest_file.parent.rmdir()
                    dest_file.parent.parent.rmdir()
                except OSError:
                    pass
            else:
                write_text(dest_file, cleaned_content)
                print(f"[UPDATED] stripped rules from: {dest_file}")

        ejected_count += 1

    for agent in unknown_agents:
        print(
            f"[ERROR] Unknown agent key: '{agent}'. Supported: {', '.join(AGENT_TARGET_MAP)}",
            file=sys.stderr,
        )

    if unknown_agents:
        return 1

    if getattr(args, "dry_run", False):
        print(f"\n[SUCCESS] Preview complete: {ejected_count} agent file(s) would be cleaned.")
    else:
        print(f"\n[SUCCESS] Successfully ejected rules from {ejected_count} agent file(s).")
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

    # Detect
    p_detect = subparsers.add_parser(
        "detect",
        help="Report which AI tools this project already shows evidence of using (read-only)",
    )
    p_detect.add_argument("--dir", default=".", help="Target project root directory")
    p_detect.add_argument(
        "--fail-if-empty",
        action="store_true",
        help="Exit with code 1 if no tool signatures are detected (default: exit 0 with notice)",
    )

    # Inject
    p_inject = subparsers.add_parser("inject", help="Inject rules into agent context files")
    p_inject.add_argument("--dir", default=".", help="Target project root directory")
    p_inject.add_argument(
        "--agents",
        required=True,
        help="Comma-separated agent keys to inject into: "
             f"{', '.join(AGENT_TARGET_MAP)}. "
             "Deliberately has no default: injecting into a tool the user does not "
             "use litters their repository, so the target set must be an explicit "
             "decision (run 'detect' first, then confirm with the user).",
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
    p_inject.add_argument(
        "--dry-run",
        action="store_true",
        help="Show exactly which files would be created or updated, with their size "
             "delta, and write nothing. Preview and write share one code path, so "
             "the preview cannot disagree with the real run.",
    )
    p_inject.add_argument(
        "--max-rule-len",
        type=int,
        default=200,
        help="Maximum character length per extracted summary rule (default: 200, 0 to disable truncation)",
    )

    # Eject
    p_eject = subparsers.add_parser("eject", help="Eject injected rules from agent context files")
    p_eject.add_argument("--dir", default=".", help="Target project root directory")
    p_eject.add_argument(
        "--agents",
        required=True,
        help=f"Comma-separated agent keys to eject rules from: {', '.join(AGENT_TARGET_MAP)}",
    )
    p_eject.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview eject changes without modifying files",
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

    try:
        if args.subcommand == "init":
            return cmd_init(args)
        elif args.subcommand == "detect":
            return cmd_detect(args)
        elif args.subcommand == "inject":
            return cmd_inject(args)
        elif args.subcommand == "eject":
            return cmd_eject(args)
        elif args.subcommand == "validate":
            return cmd_validate(args)
    except RuleIOError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

