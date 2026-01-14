# Resume as Code

CLI tool for git-native resume generation from structured work units.

## Documentation

- [Philosophy](./docs/philosophy.md) — Why "Resume as Code" works
- [Data Model](./docs/data-model.md) — Work Units, Positions, and other entities
- [Workflow Guide](./docs/workflow.md) — The Capture → Validate → Plan → Build pipeline

See the [docs folder](./docs/) for the complete documentation.

## Installation

```bash
uv sync --all-extras
```

### Platform Requirements

**macOS (PDF Generation):**

WeasyPrint requires system libraries for PDF generation. Install via Homebrew:

```bash
brew install pango cairo
```

If you encounter `OSError: cannot load library 'libpango-1.0-0'`, set the library path:

```bash
export DYLD_LIBRARY_PATH="$(brew --prefix)/lib:$DYLD_LIBRARY_PATH"
```

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) for persistence.

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
