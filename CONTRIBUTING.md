# Contributing to stripewrap

Thank you for your interest in contributing! This document covers everything
you need to get a working development environment and submit a pull request.

## Development Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/stripe
cd stripe

# 2. Create a virtual environment (Python 3.10+)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install in editable mode with all dev dependencies
pip install -e ".[dev]"

# 4. Verify everything works
pytest tests/ -v
```

## Code Standards

All contributions must pass three checks before a PR will be merged:

| Tool | Purpose | Command |
|---|---|---|
| `ruff check` | Linting | `ruff check src/ tests/` |
| `ruff format` | Formatting | `ruff format src/ tests/` |
| `mypy` | Type checking | `mypy src/` |

Run them all at once:

```bash
ruff check src/ tests/ && mypy src/
```

- Line length: 100 characters
- Python minimum: 3.10+
- All public API must have type annotations

## Writing Tests

- All tests live in `tests/`
- Use `respx` to mock HTTP calls — never make real Stripe API calls in tests
- Aim to keep coverage above 85%
- Async tests use `pytest-asyncio` with `asyncio_mode = "auto"` (no decorator needed)

```bash
pytest tests/ -v --cov=stripewrap
```

## Commit Messages

Please follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for SetupIntent resource
fix: handle missing request_id in error response
docs: add Flask webhook example
test: cover pagination edge case with empty final page
chore: bump httpx to 0.28
```

## Pull Request Process

1. **Open an issue first** for significant changes to align on approach
2. **Branch from `main`**: `git checkout -b feat/my-feature`
3. **Write tests** for any new or changed behavior
4. **Update `CHANGELOG.md`** under `[Unreleased]`
5. Ensure CI passes (green checks on the PR)
6. Request a review

## Adding a New Stripe Resource

To add a new resource (e.g., `SetupIntents`):

1. Add Pydantic model(s) to `src/stripewrap/models.py`
2. Add a resource class to `src/stripewrap/client.py` (and `async_client.py`)
3. Export from `src/stripewrap/__init__.py`
4. Add tests in `tests/test_client.py` and `tests/test_async_client.py`
5. Add an example in `examples/`
6. Update the API Coverage table in `README.md`

## Releasing (Maintainers Only)

1. Update version in `pyproject.toml`
2. Move `[Unreleased]` section in `CHANGELOG.md` to the new version number
3. Commit: `git commit -m "chore: release v0.2.0"`
4. Tag: `git tag v0.2.0 && git push origin v0.2.0`
5. CI publishes to PyPI automatically via Trusted Publishing (no token required)

## Questions?

Open a [GitHub Discussion](https://github.com/E339-art/stripe/discussions) or file an issue.
