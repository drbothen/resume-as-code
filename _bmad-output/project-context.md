---
project_name: 'Resume as Code'
user_name: 'Joshua Magady'
date: '2026-01-10'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 32
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns for implementing Resume as Code. Focus on unobvious details._

---

## Technology Stack & Versions

| Technology | Version | Notes |
|------------|---------|-------|
| Python | ≥3.10 | Required for union types, match statements |
| Click | ≥8.1 | CLI framework |
| Pydantic | ≥2.0 | V2 syntax (model_validator, not validator) |
| ruamel.yaml | ≥0.18 | Preserves comments, use instead of PyYAML for writes |
| jsonschema | ≥4.20 | Schema validation |
| WeasyPrint | ≥60 | PDF generation |
| sentence-transformers | ≥2.2 | all-MiniLM-L6-v2 model |
| Rich | ≥13 | CLI output |
| Ruff | Latest | Linting + formatting |
| mypy | Latest | Strict mode required |

---

## Critical Implementation Rules

### Python Language Rules

- **Type hints required** on all public functions and methods
- **Use `|` union syntax** not `Union[]` (Python 3.10+)
- **Prefer `from __future__ import annotations`** for forward references
- **Never use `print()`** — use Rich console from `utils/console.py`
- **Exception handling**: Catch specific exceptions, never bare `except:`
- **Async**: Not used in this project — all operations are synchronous

### CLI Framework Rules (Click)

- **One command per file** in `commands/` directory
- **Use `@click.option`** with explicit `--help` text
- **Always include `--json` flag** for machine-readable output
- **Exit codes**: 0=success, 1=error, 2=invalid args
- **Use `click.echo()` only for raw output**, Rich for formatted

### Data Model Rules (Pydantic)

- **Use `model_validator(mode='after')`** not deprecated `@validator`
- **Field names use snake_case** in Python, same in YAML
- **Optional fields**: Use `field: str | None = None` pattern
- **Validation errors**: Catch `ValidationError`, convert to `ResumeError`

### YAML Rules

- **Read**: Use `yaml.safe_load()` from PyYAML
- **Write**: Use `ruamel.yaml` to preserve comments and formatting
- **Field names**: Always snake_case (`skills_demonstrated` not `skillsDemonstrated`)
- **IDs**: Format `wu-{YYYY-MM-DD}-{slug}` for Work Units

---

## Testing Rules

### Test Organization

```
tests/
├── conftest.py          # Shared fixtures only
├── test_cli.py          # CLI integration tests
├── unit/                # Unit tests mirror src/
│   └── test_{module}.py
└── fixtures/            # Test data files
```

### Test Naming

```python
# Pattern: test_{function}_{scenario}_{expected}
def test_validate_work_unit_missing_problem_raises_error():
    ...
```

### CLI Testing

```python
from click.testing import CliRunner

def test_plan_command_shows_selections():
    runner = CliRunner()
    result = runner.invoke(cli, ["plan", "--jd", "test.txt"])
    assert result.exit_code == 0
```

### Coverage

- Run with `pytest --cov=resume_as_code`
- No strict threshold, but test all public APIs

---

## Code Quality Rules

### Before Any Commit

```bash
ruff check src tests --fix  # Lint and auto-fix
ruff format src tests       # Format
mypy src --strict           # Type check with zero errors
pytest                      # All tests pass
```

### File Naming

| Type | Convention | Example |
|------|------------|---------|
| Modules | snake_case | `work_unit.py` |
| Classes | PascalCase | `WorkUnit` |
| Functions | snake_case | `load_work_units()` |
| Constants | UPPER_SNAKE | `DEFAULT_CONFIG` |
| Test files | test_{module}.py | `test_ranker.py` |

### Import Order (Ruff handles this)

1. Standard library
2. Third-party
3. Local imports (relative)

---

## Architecture Boundaries

### Layer Rules

```
commands/  → CLI I/O only, delegates to services
services/  → All business logic, no CLI dependencies
models/    → Pure data structures, Pydantic validation
providers/ → Output generation, receives models, returns bytes
utils/     → Pure utility functions, no side effects
```

### What Goes Where

| Need | Location |
|------|----------|
| New CLI command | `commands/{name}.py` |
| Business logic | `services/{domain}.py` |
| Data structure | `models/{entity}.py` |
| Output format | `providers/{format}.py` |
| Helper function | `utils/{category}.py` |

---

## Error Handling

### Exception Hierarchy

```python
class ResumeError(Exception):
    exit_code: int = 1

class ValidationError(ResumeError):
    exit_code = 1

class ConfigurationError(ResumeError):
    exit_code = 2

class RenderError(ResumeError):
    exit_code = 1
```

### CLI Error Pattern

```python
try:
    result = service.do_thing()
except ValidationError as e:
    console.print(f"[red]✗[/red] {e.message}")
    raise SystemExit(e.exit_code)
```

---

## Critical Don't-Miss Rules

### NEVER Do

- ❌ Use `print()` — always Rich console
- ❌ Put business logic in commands
- ❌ Use camelCase in YAML fields
- ❌ Skip type hints on public functions
- ❌ Catch bare `Exception`
- ❌ Import from commands in services (circular)

### ALWAYS Do

- ✅ Run ruff + mypy before completing any task
- ✅ Use `console.print("[red]✗[/red]")` for errors
- ✅ Add tests for new functionality
- ✅ Use snake_case everywhere (Python and YAML)
- ✅ Follow the exception hierarchy
- ✅ Keep commands thin, services thick

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Reference the architecture document for detailed decisions

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review periodically for outdated rules
- Remove rules that become obvious over time

---

_Last Updated: 2026-01-10_
