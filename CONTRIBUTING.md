# Contributing to Project Architect

Thank you for your interest in contributing to Project Architect.

## Core Architectural Invariants

All contributions must adhere to the following design baselines:
1. **Zero External Runtime Dependencies**: The core scaffolding and injection engine must strictly rely on the Python 3 standard library (Python 3.8+ compatible).
2. **Zero Emoji Policy**: Code, comments, commit messages, and documentation must not contain any emojis.
3. **Non-Invasive Marker Isolation**: Any multi-agent rule injection must respect paired boundary markers (`<!-- RULES START -->` and `<!-- RULES END -->`) and never overwrite user-defined private configurations outside the markers.
4. **Data-Driven & Quantified**: Architecture recommendations and tech stack matrices must be grounded in measurable engineering metrics (latency, binary size, memory usage, QPS).

## Development and Testing

### Setup Environment
Project Architect requires Python 3.8 or higher. No third-party packages are required to run the core tool.

To run tests:
```bash
# Run unit tests using Python standard unittest
python -m unittest discover -s tests -p "test_*.py" -v

# Or run via pytest if installed
pytest -v
```

### Code Style and Formatting
- Follow PEP 8 guidelines.
- Keep functions modular and single-purpose.
- Write unit tests for any new CLI options, marker edge cases, or agent context mappings.

## Commit Message Guidelines

We follow a strict, concise commit convention:
- Subject line: <= 50 characters, imperative mood, capitalized, no ending period (e.g. `Add Windows path normalization to marker injector`).
- Blank line separating subject and body.
- Body: <= 72 characters per line, explaining the "why" and non-obvious context.
- No meta-commentary, no emojis, no diff duplication.

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Ensure all automated unit tests pass locally.
3. If adding a new agent context format, update both `scripts/scaffold_rules.py` (mapping and tests) and `references/agent-rules-mapping.md`.
4. Open a Pull Request with a clear description of the problem solved.
