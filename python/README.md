# Liman Python

Python monorepo with multiple packages for building AI agents.

## Packages

- [**liman**](packages/liman): Main package with agent orchestration and executor - use as entry point
- [**liman_core**](packages/liman_core): Core library with nodes and YAML processing
- [**liman_finops**](packages/liman_finops): OpenTelemetry instrumentation and cost tracking
- [**liman_openapi**](packages/liman_openapi): OpenAPI to ToolNode generation

## Development

```bash
poe lint      # check formatting and linting
poe format    # auto-format
poe test      # run tests
poe mypy      # type-check
poe coverage  # run tests with coverage report
```

## How to generate code references

```bash
python ./scripts/griffe_libraries.py
```
