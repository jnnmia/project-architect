# Project Architect

[English](./README.en.md) | [简体中文](./README.md)

[![skills.sh](https://img.shields.io/badge/skills.sh-project--architect-000000?logo=vercel&logoColor=white)](https://skills.sh/jnnmia/project-architect)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/jnnmia/project-architect/releases)
[![CI](https://img.shields.io/badge/build-passing-brightgreen.svg)](.github/workflows/ci.yml)

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
Constitutional Single Source of Truth: `.specify/memory/constitution.md`
Binding Architectural & Quality Invariants:
### I. Static Compilation
- Core logic MUST compile into a single static binary with zero dynamic C-runtime dependencies.
### II. Layer Decoupling
- Parser and Renderer modules MUST maintain strict interface-level isolation.
### III. Structured Errors
- File I/O errors MUST return line-numbered structured diagnostics. Panic calls are forbidden.

Hard Execution Gates:
1. Every proposed plan MUST pass the Constitution Check gate with Evidence.
2. Automated test suite and scope guards are non-negotiable hard gates.
<!-- RULES END -->
```

---

### Mode 2: Standalone Terminal Execution (CLI Mode)

Suitable for CI/CD pipelines, headless environments, or developers who prefer command-line automation.

#### Prerequisites
- Python 3.8+ (standard library only; zero external pip dependencies).
- Git.

#### 3-Step Pipeline

```bash
# Step 1: Initialize ground rules and planning templates (init)
# Generates .specify/memory/constitution.md, spec/plan/tasks templates, and baseline AGENTS.md
python scripts/scaffold_rules.py init \
  --dir /path/to/project \
  --name "my-service" \
  --purpose "High-throughput log parser"

# Step 2: Incrementally inject rules into agent context files (inject)
# Parses MUST constraints from ground rules and injects summary inside boundary markers
python scripts/scaffold_rules.py inject \
  --dir /path/to/project \
  --agents "agents,claude,cursor"

# Step 3: Verify governance compliance (validate)
# Ensures no unresolved placeholders remain, MUST keywords exist, and rationales are provided
python scripts/scaffold_rules.py validate \
  --dir /path/to/project
```

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
skills/project-architect/
├── SKILL.md                          # Skill metadata and core workflow
├── README.md                         # Chinese documentation
├── README.en.md                      # English documentation
├── LICENSE                           # MIT License
├── CONTRIBUTING.md                   # Collaboration and contributing guidelines
├── pyproject.toml                    # Package configuration and pytest parameters
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

Issues and Pull Requests are welcome. Before contributing, please review [CONTRIBUTING.md](CONTRIBUTING.md):
- Strictly maintain zero external runtime dependencies (Python standard library only).
- Strictly adhere to the zero-emoji policy.
- Follow the concise commit message guidelines.
- Add unit tests for any new features or bug fixes.

---

## Changelog

| Version | Release Date | Description |
|---|---|---|
| **v1.0.0** | 2026-09-15 | Baseline release. Features five-stage architectural workflow, ground rules scaffolding, multi-agent marker injection, automated test suite, open-source documentation, and working CLI example. |

---

## License

This project is licensed under the [MIT License](LICENSE).
