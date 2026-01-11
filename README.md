# Resume as Code

CLI tool for git-native resume generation from structured work units.

## Installation

```bash
uv sync --all-extras
```

## Usage

```bash
uv run resume --help
```

## Development

```bash
# Run tests
uv run pytest

# Code quality
uv run ruff check src tests --fix
uv run ruff format src tests
uv run mypy src --strict
```
