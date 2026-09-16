# Example: Minimal CLI (AudioClip)
[![skills.sh](https://skills.sh/b/jnnmia/project-architect)](https://skills.sh/jnnmia/project-architect)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/jnnmia/project-architect/actions/workflows/ci.yml/badge.svg)](https://github.com/jnnmia/project-architect/actions)


This directory showcases an actual project initialized and governed by `project-architect`.

## Directory Layout
- `.specify/memory/constitution.md`: The single source of truth containing non-negotiable architectural principles.
- `AGENTS.md`: The cross-agent entry point referencing the constitution.
- `CLAUDE.md`: Demonstrates non-invasive rule injection. Custom developer instructions remain intact above the `<!-- RULES START -->` marker.
- `.cursor/rules/project-rules.mdc`: Demonstrates Cursor IDE rule format with required YAML frontmatter (`alwaysApply: true`).
- `templates/`: Work planning templates (`plan-template.md`, `spec-template.md`, `tasks-template.md`) with evidence gates.

## Validation
To validate this example:
```bash
python ../../scripts/scaffold_rules.py validate --dir .
```
