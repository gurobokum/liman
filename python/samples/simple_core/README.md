# simple_core

A low-level sample showing how to build an agent directly with `liman_core`, without any higher-level abstractions.

Demonstrates:

- Loading nodes from YAML specs
- Dependency injection with `registry.provide()` and `FromLiman[T]`
- Manual orchestration of LLM and tool nodes via `NodeActor`

## What it does

The agent answers weather questions for the user's current location. The location is resolved by an injected `LocationService` — the LLM never sees it as a tool argument. The temperature unit is chosen automatically based on the location (Fahrenheit for the US, Celsius elsewhere).

## Setup

Copy the example env file and add your OpenAI key:

```bash
cp .env.example .env
```

Install dependencies:

```bash
uv sync
```

## Run

```bash
uv run python src/main.py
```

to see detailed debug output use

```bash
LIMAN_DEBUG=1 uv run python src/main.py
```

Type `exit` or press `Ctrl-C` to quit.
