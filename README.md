# Project Architect

[![skills.sh](https://skills.sh/b/jnnmia/project-architect)](https://skills.sh/jnnmia/project-architect) [![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](https://github.com/jnnmia/project-architect/releases) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

English | [简体中文](./README.zh-CN.md)

Project Architect is an engineering governance and architecture scaffolding tool designed for AI-assisted software development. It guides technology stack selection through quantified decision trees, establishes non-negotiable project ground rules as hard constraints, and synchronizes rules across Cursor, Claude Code, GitHub Copilot, and Gemini CLI using non-invasive boundary markers.

---

## Table of Contents

- [Why Project Architect](#why-project-architect)
- [Core Mechanics](#core-mechanics)
- [Supported AI Agents](#supported-ai-agents)
- [Installation & Activation](#installation--activation)
- [Usage Guide](#usage-guide)
  - [Mode 1: Interactive AI Dialogue (Skill Mode, Recommended)](#mode-1-interactive-ai-dialogue-skill-mode-recommended)
  - [Mode 2: Standalone Terminal Execution (CLI Mode)](#mode-2-standalone-terminal-execution-cli-mode)
- [Project Topology](#project-topology)
- [Automated Testing](#automated-testing)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## Why Project Architect

When developing software alongside AI agents, developers frequently face three failure modes:

1. **Stack Bloat**: When asked to build a simple utility, AI models often pull in heavyweight runtimes, web frameworks, and unverified third-party libraries.
2. **Context Drift**: Layering separation and test-first constraints agreed upon at turn 1 are often discarded after turn 5, resulting in circular imports and ungated code changes.
3. **Prompt Overwrites**: Primitive rule sync scripts blindly overwrite target files, destroying custom prompt additions, aliases, and developer preferences in `CLAUDE.md` or `.cursor/rules/`.

Project Architect formalizes architectural constraints into a single source of truth (`constitution.md`), enforces verifiable implementation evidence in task plans, and performs marker-bounded rule injection so projects retain their architectural boundaries over extended agent sessions.

---

## Core Mechanics

### 1. Ground Rules as Hard Constraints
Project ground rules reside at `.specify/memory/constitution.md` using declarative RFC 2119 keywords (`MUST` / `MUST NOT`). Any proposed plan or code change that breaches ground rules is flagged as a critical blocker and must be revised.

### 2. Zero-Invasive Marker Isolation
All injected rules are wrapped inside paired boundary markers (`<!-- RULES START -->` and `<!-- RULES END -->`). Only content between the markers is managed by Project Architect; developer configurations outside the markers (such as custom build scripts, test aliases, or prompt tuning) remain untouched.

### 3. Data-Driven Tradeoffs & Checkpoints
Subjective statements are rejected. Technology choices must cite measurable metrics: cold-start latency, memory overhead, binary footprint, or dependency count. Planning templates require concrete implementation evidence before proceeding to code generation.

---

## Supported AI Agents

Project Architect distributes rules to major AI programming environments:

| Tool | Target Context File | Injection Strategy |
|---|---|---|
| **Universal Agents** | `AGENTS.md` | Marker-wrapped single entry point across agents |
| **Claude Code** | `CLAUDE.md` | Marker-wrapped, preserving user header commands |
| **Cursor IDE** | `.cursor/rules/project-rules.mdc` | Automatically injects YAML frontmatter (`alwaysApply: true`) |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Marker-wrapped repository-wide guidelines |
| **Google Gemini CLI** | `GEMINI.md` | Marker-wrapped global and project rules |
| **Windsurf** | `.windsurf/rules/project-rules.md` | Marker-wrapped Cascade engine rule directory |
| **Trae** | `.trae/rules/project_rules.md` | Marker-wrapped ByteDance Trae context |

### Inject Only What You Use

The table above lists *capabilities*, not defaults. Writing rule files is a change to
someone else's repository: handing a Cursor-only project a `.trae/rules/` directory, a
`.windsurf/rules/` directory and a `GEMINI.md` is repository pollution, not thoroughness.

So the target set is always a confirmed subset, in three steps:

1. **Detect** — `scaffold_rules.py detect` scans the project for on-disk traces of each
   tool. It is strictly read-only and writes nothing.
2. **Confirm** — the agent shows you what it found and asks which tools you actually use.
   The scan is evidence, not consent: finding a trace never authorises writing to it, and
   a brand-new project (no traces at all) is exactly when asking matters most.
3. **Inject** — `--agents` carries only the keys you confirmed. A tool you did not mention
   is never touched, even if it was detected.

`AGENTS.md` is the exception: it is the tool-agnostic entry point that `init` creates
anyway, so it can ride along as a default. The other six targets must each be confirmed.

`--agents` has **no default value** for this reason. Omitting it is an error
(exit code `2`) rather than a silent injection of a whole rule set.

---

## Installation & Activation

Project Architect is published as a standard Agent Skill. You can install it directly into any compatible agent runtime (Claude Code, Cursor, Gemini CLI, etc.) using the `npx skills` package manager:

### 1. Skills CLI One-Line Install (Recommended)

```bash
# Install to current project (local workspace only)
npx skills add jnnmia/project-architect

# Or install globally (available across all compatible agents on the machine)
npx skills add jnnmia/project-architect -g -y

# Or install via full GitHub repository URL
npx skills add https://github.com/jnnmia/project-architect.git -g -y
```

### 2. Ask Your AI Agent to Install

Send the following instruction to your AI assistant:

```text
Please install the project-architect Skill for me.
Repository: https://github.com/jnnmia/project-architect
If you support skills CLI, run: npx skills add jnnmia/project-architect
Otherwise, please clone or copy the repository into your skills directory with directory name 'project-architect', ensuring SKILL.md is at the root.
```

### 3. Manual Git Clone

Clone into your runtime's skills directory (replace `<SKILLS_DIR>` with your agent's skills path, e.g. `~/.gemini/config/skills` or `~/.agents/skills`):

```bash
git clone https://github.com/jnnmia/project-architect.git <SKILLS_DIR>/project-architect
```

---

## Usage Guide

Project Architect supports two operating modes: interactively within AI chat sessions (recommended, zero CLI commands needed), or as a standalone CLI tool in your terminal.

### Mode 1: Interactive AI Dialogue (Skill Mode, Recommended)

With the skill installed (via `npx skills add jnnmia/project-architect`), you do not need to memorize or run any Python commands. Simply paste one of the prompt templates into your conversation with Cursor, Claude, or Gemini:

#### Prompt Templates

```text
# Scenario A: Scaffold a new project and define ground rules
Please use project-architect to help me bootstrap a new project: I want to build a local audio slicer utility. Please guide me through non-functional metrics, evaluate technology options, and establish ground rules.

# Scenario B: Extract architecture invariants from an existing repository
Please use project-architect to inspect the current project, extract core layering boundaries and non-negotiable constraints, and inject them into CLAUDE.md and .cursor/rules/.

# Scenario C: Pre-commit checkpoint review on an implementation plan
Please use project-architect to review my current plan (plan.md), checking implementation evidence against our ground rules and highlighting architectural risks.
```

#### Interactive Workflow Walkthrough

When you trigger project initialization, the agent follows a structured decision tree:

```text
[Developer]
I want to build a CLI utility to batch-convert Markdown files into PDFs. Help me scaffold the project.

[Agent questions NFRs along the decision tree]
Understood. Before fixing architecture rules, let us clarify one key constraint:
Does the tool require complex print styling (custom headers/footers, dynamic page numbers, CSS paged media), or is it focused on fast, plain document conversion?
- Option A (Recommended): Lightweight single-binary renderer (cold-start < 30ms, binary < 20MB, zero browser runtime dependencies).
- Option B: Headless browser renderer (supports full CSS, but requires Chromium runtime, distribution size > 150MB).

[Developer]
Let us go with Option A. It must be a self-contained single binary with zero external dependencies.

[Agent asks which tools to configure, after scanning the project for existing traces]
One more decision before I write anything: which AI tools do you use with this repository?
- Option A (Recommended): Cursor and Claude Code — the two you are working in now.
- Option B: also configure GitHub Copilot, Gemini CLI, Windsurf or Trae.
Rule files are written only for the tools you name. I will not drop .trae/ or .windsurf/ directories into a repository that does not use them.

[Developer]
Just Cursor and Claude Code.

[Agent locks stack, generates ground rules, and executes scaffolding in background]
Stack locked: Go 1.22 + pure Go document renderer.
Establishing 3 non-negotiable ground rules:
1. Static Compilation: Core logic MUST compile into a single static binary with zero dynamic C-runtime dependencies.
2. Layer Decoupling: Parser and Renderer modules MUST maintain strict interface-level isolation.
3. Structured Errors: File I/O errors MUST return line-numbered structured diagnostics. Panic calls are forbidden.

[Agent finishes file generation and reports status]
Scaffolded .specify/memory/constitution.md and distributed rules to AGENTS.md, CLAUDE.md, and .cursor/rules/.
```

#### Rule Injection Demonstration (Example: CLAUDE.md)

Before injection, developer-defined commands exist at the top of the file:
```markdown
# My Developer Setup
- test: go test -v ./...
- lint: golangci-lint run
```

After injection, user configurations are fully preserved, and project rules are neatly enclosed within markers:
```markdown
# My Developer Setup
- test: go test -v ./...
- lint: golangci-lint run

<!-- RULES START -->
## Project Governance & Principles (Automated)
Rules Source of Truth: `.specify/memory/constitution.md`

### Core Architectural & Quality Invariants:
#### 1. Static Compilation
- Core logic MUST compile into a single static binary with zero dynamic C-runtime dependencies.
#### 2. Layer Decoupling
- Parser and Renderer modules MUST maintain strict interface-level isolation.
#### 3. Structured Errors
- File I/O errors MUST return line-numbered structured diagnostics. Panic calls are forbidden.

### Engineering Checkpoints:
1. Verify proposed plans against core project rules.
2. Maintain automated test coverage for critical business logic.
3. Keep rule updates within boundary markers without overwriting custom configurations.
<!-- RULES END -->
```

---

### Mode 2: Standalone Terminal Execution (CLI Mode)

Suitable for CI/CD pipelines, headless environments, or developers who prefer command-line automation.

#### Prerequisites
- Python 3.8+ (standard library only; zero external pip dependencies).
- Git.

> **Run every command from the skill root.** `scaffold_rules.py` locates its templates
> relative to its own location, so execute it from the directory that holds both
> `scripts/` and `assets/templates/`. Only `--dir` points at your target project.

> **Not a pip package.** This repository is distributed as an Agent Skill, not as an
> installable Python distribution. Templates live in `assets/templates/` next to the
> script, so `pip install` / `pipx install` are not supported — clone the repository
> (or install it as a skill) and invoke the script in place.

#### 5-Step Pipeline

```bash
# Step 1: Detect which AI tools this project already shows traces of (detect, read-only)
# Reports one line per supported tool; writes nothing. Ask the user which of them they
# actually use before going any further.
python scripts/scaffold_rules.py detect \
  --dir /path/to/project

# Step 2: Initialize ground rules and planning templates (init)
# Generates .specify/memory/constitution.md, spec/plan/tasks templates, and baseline AGENTS.md
python scripts/scaffold_rules.py init \
  --dir /path/to/project \
  --name "my-service" \
  --purpose "High-throughput log parser"

# Step 3: Verify governance compliance (validate)
# Ensures no unresolved placeholders remain, MUST keywords exist, and rationales are provided.
# Validating before the first injection keeps an unvetted constitution from being
# spread across every context file.
python scripts/scaffold_rules.py validate \
  --dir /path/to/project

# Step 4: Preview the injection (inject --dry-run)
# Reports whether each target would be created or updated, with the size delta.
# --agents is REQUIRED: list only the tools the user confirmed, never the full set.
python scripts/scaffold_rules.py inject \
  --dir /path/to/project \
  --agents "agents,claude,cursor" \
  --strict --dry-run

# Step 5: Apply for real, once the preview looks right
python scripts/scaffold_rules.py inject \
  --dir /path/to/project \
  --agents "agents,claude,cursor" \
  --strict
```

> `--dry-run` writes nothing: it reports whether each target would be created or
> updated, with the size delta. Preview and write share one code path, so the
> preview cannot disagree with the real run. To roll back an applied change,
> delete the block between `<!-- RULES START -->` and `<!-- RULES END -->`.

#### Exit Codes

Scripted callers must branch on the exit code rather than matching output text.

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Rule-level failure: validation errors, no principles extracted under `--strict`, an unrecognised `--agents` key, or `detect` finding no tool trace at all |
| `2` | I/O failure (unreadable or unwritable constitution, missing asset template, non-UTF-8 target file), a `--constitution-path` escaping the project root, or a missing required `--agents` |

All generated files are written as **UTF-8 without BOM, LF line endings**, so the same
input produces byte-identical output on Windows and Linux.

#### Terminal Execution Sample Output

```bash
$ python scripts/scaffold_rules.py init --dir ./md2pdf --name "md2pdf" --purpose "Lightweight conversion CLI"
[CREATED] Constitution initialized at: ./md2pdf/.specify/memory/constitution.md
[CREATED] Template copied to: ./md2pdf/templates/plan-template.md
[CREATED] Template copied to: ./md2pdf/templates/spec-template.md
[CREATED] Template copied to: ./md2pdf/templates/tasks-template.md
[CREATED] Baseline AGENTS.md created at: ./md2pdf/AGENTS.md
[SUCCESS] Project rule scaffolding complete.

$ python scripts/scaffold_rules.py inject --dir ./md2pdf --agents "agents,claude,cursor"
[INJECTED] Updated agent context: ./md2pdf/AGENTS.md
[INJECTED] Updated agent context: ./md2pdf/CLAUDE.md
[INJECTED] Updated agent context: ./md2pdf/.cursor/rules/project-rules.mdc
[SUCCESS] Successfully injected rules into 3 agent file(s).

$ python scripts/scaffold_rules.py validate --dir ./md2pdf
[PASS] Constitution './md2pdf/.specify/memory/constitution.md' meets all governance criteria.
```

---

## Project Topology

```text
project-architect/
├── SKILL.md                          # Skill metadata and core workflow
├── README.md                         # English documentation
├── README.zh-CN.md                   # Chinese documentation
├── LICENSE                           # MIT License
├── CONTRIBUTING.md                   # Collaboration and contributing guidelines
├── pyproject.toml                    # Project metadata and pytest parameters (not a pip package)
├── .gitignore                        # Git ignore patterns
├── .github/workflows/ci.yml          # GitHub Actions CI workflow
├── scripts/
│   └── scaffold_rules.py             # Scaffolding and marker injection engine
├── references/
│   ├── constitution-guide.md         # Ground rules authoring guide
│   ├── tech-stack-decision-matrix.md # Quantified tech stack selection matrix
│   └── agent-rules-mapping.md        # AI context file mapping details
├── assets/templates/
│   ├── constitution-template.md      # Baseline ground rules template
│   ├── plan-template.md              # Plan template with evidence checks
│   ├── spec-template.md              # Specification template
│   └── tasks-template.md             # Task breakdown with test gates
├── tests/
│   └── test_scaffold_rules.py        # Automated test suite (init/inject/validate)
└── examples/minimal-cli/             # Complete sample project demonstration
```

---

## Automated Testing

Project Architect includes a test suite covering initialization, idempotency, marker recovery, frontmatter handling, and error detection.

```bash
# Run with Python standard unittest
python -m unittest discover -s tests -p "test_*.py" -v

# Or run with pytest
pytest -v
```

---

## Contributing

Issues and Merge Requests are welcome. Before contributing, please review the development baseline:
- Strictly maintain zero external runtime dependencies (Python standard library only).
- Strictly adhere to the zero-emoji policy.
- Follow the concise commit message guidelines.
- Add unit tests for any new features or bug fixes.

---

## Changelog

| Version | Release Date | Description |
|---|---|---|
| **v1.1.0** | 2026-09-18 | Adds a read-only `detect` subcommand and a `--dry-run` preview for injection. `inject` now requires an explicit `--agents` list instead of defaulting to a broad set, so rule files are never written for tools a project does not use. Fixes platform-dependent output (UTF-8/LF, byte-identical on Windows and Linux), blocks `--constitution-path` from escaping the project root, and parses constitutions written as level-2 sections. `pip install` is no longer declared as a supported channel. Test suite: 13 → 61 cases. |
| **v1.0.1** | 2026-09-15 | Refined wording in core descriptions and templates to eliminate AI buzzwords, streamlined rule injection prompts, and updated verification checklists. |
| **v1.0.0** | 2026-09-15 | Baseline release. Features five-stage architectural workflow, ground rules scaffolding, multi-agent marker injection, automated test suite, open-source documentation, and working CLI example. |
