# Contributing to Forge

## Development Setup

1. Clone the repo and install dependencies:
```bash
git clone https://github.com/nautilus4707/Forge.git
cd Forge
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[all,dev]"
```

2. Set up API keys in `.env` (copy from `.env.example`)

3. Run tests:
```bash
pytest tests/ -v
```

## Code Style

We use `ruff` for linting and formatting:
```bash
ruff check forge/
ruff format forge/ tests/
```

## Adding a New Tool

1. Create `forge/tools/builtin/your_tool.py`
2. Implement an async function and `register_tools(registry)`
3. Import in `forge/tools/registry.py` `load_builtins()`
4. Add tests in `tests/unit/test_tools.py`

## Adding a New Model Provider

1. Add the provider to `ModelProvider` enum in `forge/core/types.py`
2. Add routing logic in `forge/models/router.py`
3. Add cost data in `forge/models/cost.py`

## Pull Request Process

1. Create a feature branch from `master`
2. Write tests for new functionality
3. Ensure all tests pass: `pytest tests/ -v`
4. Format code: `ruff format forge/ tests/`
5. Submit PR with clear description
