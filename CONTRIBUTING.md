# Contributing to project-architect

Thank you for your interest in contributing to project-architect.

## Core Architectural Invariants

All contributions must adhere to the following design baselines:
1. **Zero External Runtime Dependencies**: Core helper scripts should prefer the Python standard library unless external tools are explicitly justified.
2. **Zero Emoji Policy**: Code, comments, commit messages, and documentation must not contain any emojis.
3. **Runtime Neutrality**: Agent skill instructions must remain neutral across Claude Code, Cursor, Gemini CLI, and other 50+ agent environments.
4. **Data-Driven & Quantified**: Technical tradeoffs must cite measurable engineering indicators (latency, memory, packaging size).

## Development and Testing

### Setup Environment
Requires Python 3.8 or higher. No third-party packages are required to run core tools.

To run tests:
```bash
# Run unit tests using Python standard unittest
python -m unittest discover -s tests -p "test_*.py" -v
```

### Code Style and Formatting
- Follow PEP 8 guidelines.
- Keep functions modular and single-purpose.
- Write unit tests for any new features, flags, or boundary edge cases.

## Commit Message Guidelines

We follow a strict, concise commit convention:
- Subject line: <= 50 characters, imperative mood, capitalized, no ending period.
- Blank line separating subject and body.
- Body: <= 72 characters per line, explaining the "why" and non-obvious context.
- No meta-commentary, no emojis, no diff duplication.

## Pull Request Process

1. Fork the repository and create your feature branch.
2. Ensure all automated unit tests pass locally.
3. Keep changes focused and atomic; avoid unrelated style edits.
4. Open a Pull Request with a clear description of the problem solved.
