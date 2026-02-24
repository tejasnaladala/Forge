# Contributing to Forge

Thank you for your interest in contributing to Forge. This document describes the development workflow, coding standards, and contribution process.

---

## Code of Conduct

All contributors are expected to engage respectfully and constructively. Maintain a professional and inclusive environment in all project interactions, including issues, pull requests, and discussions.

---

## Reporting Issues

To report a bug or request a feature, open an issue on the [GitHub issue tracker](https://github.com/nautilus4707/Forge/issues). Include the following information:

- A clear, descriptive title.
- Steps to reproduce the issue (for bugs).
- Expected behavior and observed behavior.
- Python version, operating system, and Forge version (`forge --version`).
- Relevant configuration (forgefile, environment variables) with sensitive values redacted.

---

## Development Setup

### Prerequisites

- Python 3.11 or later
- Git

### Installation

Clone the repository and install all dependencies, including development tools:

```bash
git clone https://github.com/nautilus4707/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[all,dev]"
```

### Environment Configuration

Copy the example environment file and configure at least one provider API key:

```bash
cp .env.example .env
```

Edit `.env` and set the appropriate values. Refer to `.env.example` for the full list of supported variables.

### Running Tests

```bash
pytest tests/ -v
```

### Linting

```bash
ruff check forge/
```

### Formatting

```bash
ruff format forge/ tests/
```

---

## Submitting Changes

### Pull Request Process

1. Create a feature branch from `master`.
2. Implement changes with appropriate test coverage.
3. Verify all tests pass: `pytest tests/ -v`.
4. Format code: `ruff format forge/ tests/`.
5. Verify linting: `ruff check forge/`.
6. Submit a pull request with a clear description of the changes and their motivation.

Pull requests should be focused on a single concern. Avoid combining unrelated changes in one pull request.

---

## Coding Standards

Forge uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting. All submitted code must pass both linting and formatting checks before merge.

- **Line length**: 100 characters.
- **Target version**: Python 3.12+.
- **Lint rules**: `E`, `F`, `I`, `N`, `W` (pycodestyle, Pyflakes, isort, naming, warnings).

---

## Extension Guides

### Adding a New Tool

1. Create a file at `forge/tools/builtin/<tool_name>.py`.
2. Implement an async function and a `register_tools(registry)` entry point.
3. Import the registration function in `forge/tools/registry.py` within `load_builtins()`.
4. Add corresponding tests in `tests/unit/test_tools.py`.

### Adding a New Model Provider

1. Add the provider to the `ModelProvider` enum in `forge/core/types.py`.
2. Add routing logic in `forge/models/router.py`.
3. Add cost data in `forge/models/cost.py`.

---

## Review Process

All pull requests require at least one review before merging. Reviewers evaluate:

- Correctness and completeness of the implementation.
- Test coverage for new or modified functionality.
- Adherence to coding standards.
- Clarity and accuracy of documentation updates, where applicable.

---

## License

By contributing to Forge, you agree that your contributions will be licensed under the [Apache License 2.0](LICENSE).
