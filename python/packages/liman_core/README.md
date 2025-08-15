# Liman Core

[![codecov](https://codecov.io/gh/gurobokum/liman/graph/badge.svg?token=PMKWXNBF1K&component=python/liman_core)](https://codecov.io/gh/gurobokum/liman?components[0]=python/liman_core)

Core library for **Liman** - a declarative YAML-based agent framework with custom DSL for building AI workflows.

## What is it?

Liman Core provides **low-level building blocks** for creating AI agents through YAML manifests.  
This repo introduces a **Node** and **NodeActor** architecture for defining and executing agent workflows.  
**Nodes** are stateless specifications that store configuration, while **NodeActors** are stateful instances that execute specific nodes. Use these components to build your own orchestration system or use the built-in one in [liman](../liman).

## Key Features

- **YAML-First**: Define entire agent workflows in declarative YAML
- **Node Architecture**: LLM, Tool, Function, and custom nodes with automatic composition
- **Edge DSL**: Smart conditional routing between nodes with custom expressions
- **Multi-Language**: Built-in localization for prompts and descriptions
- **Plugin System**: Extensible architecture with authentication, telemetry, and custom plugins
- **NodeActor**: Async execution engine with state management and error handling

## Installation

```bash
pip install liman_core
```

Requires Python 3.10+

## Quick Example

```python
from liman_core import LLMNode, ToolNode, NodeActor, Registry

# Initialize registry
registry = Registry()

# Create tool
tool_spec = {
    "kind": "ToolNode",
    "name": "calculator",
    "func": "math.sqrt",
    "description": {"en": "Calculate square root"}
}
tool = ToolNode.from_dict(tool_spec, registry)

# Create LLM node with tool
llm_spec = {
    "kind": "LLMNode",
    "name": "assistant",
    "tools": ["calculator"],
    "prompts": {"system": {"en": "You are a math assistant"}}
}
llm_node = LLMNode.from_dict(llm_spec, registry)

# Execute with NodeActor
actor = NodeActor.create(llm_node, llm=your_llm_instance)
result = await actor.execute("What's the square root of 16?", execution_id)
```

## Core Components

### Nodes (Stateless Specifications)

- **LLMNode**: LLM requests with system prompts and tool integration
- **ToolNode**: Function definitions for LLM tool calling
- **FunctionNode**: Custom Python functions

Nodes are building blocks that store configuration and behavior but contain no execution state.

### NodeActor (Stateful Execution)

Stateful execution engine that wraps a specific node, handles state management, and executes async operations with error handling and recovery.

### Edge DSL

```yaml
nodes:
  - target: success_handler
    when: "status == 'complete' and retry_count < 3"
  - target: error_handler
    when: "failed and critical == true"
```

### Registry & Plugins

Central component registry with extensible plugin system for auth, telemetry, and custom functionality.

## Architecture

```
Registry → Node (stateless) → NodeActor (stateful) → Execution
    ↓           ↓                    ↓
 Plugins    Spec Config        State Management
```

Use `.print_spec()` on any node to inspect its YAML specification.

## Development

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
poe test

# Type checking
poe mypy

# Linting
poe lint

# Formatting
poe format
```
