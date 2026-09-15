# Example: Minimal CLI (AudioClip)

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
