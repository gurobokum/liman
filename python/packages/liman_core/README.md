# Liman Core

Core library of the Liman framework providing low-level building blocks for declarative YAML-based agent workflows with custom DSL.

## Features

- **Declarative YAML Configuration**: Define agents using simple YAML manifests
- **Multi-language Support**: Built-in localization for prompts and descriptions
- **Node-based Architecture**: Compose workflows from LLM, Tool, and custom nodes
- **Edge DSL**: Connect nodes with conditional expressions and function references

## Node Types

### LLMNode

Wraps LLM requests with system prompts and tool integration.

```yaml
kind: LLMNode
name: assistant
prompts:
  system:
    en: |
      You are a helpful assistant.
    es: |
      Eres un asistente útil.
tools:
  - calculator
nodes:
  - target: analyzer
    when: "result == 'success'"
  - target: error_handler
    when: "result != 'success' and retry_count < 3"
```

### ToolNode

Defines function calls for LLM tool integration.

```yaml
kind: ToolNode
name: calculator
description:
  en: |
    Performs mathematical calculations
func: my_module.calculate
arguments:
  - name: expression
    type: str
    description:
      en: Mathematical expression to evaluate
```

## Installation

```bash
pip install liman_core
```

## Quick Start

```python
from liman_core import LLMNode, ToolNode

# Load from YAML
llm_node = LLMNode.from_yaml_path("agent.yaml")

# Create from dict
tool_spec = {
    "kind": "ToolNode",
    "name": "calculator",
    "description": {"en": "Math tool"},
    "func": "math.sqrt"
}
tool_node = ToolNode.from_dict(tool_spec)

# Compile and invoke
llm_node.compile()
result = llm_node.invoke("What is the square root of 16?")
```

## Edge DSL

Connect nodes using the custom DSL for conditional execution:

```yaml
nodes:
  # Simple target reference
  - analyzer

  # Conditional execution with variables
  - target: success_handler
    when: "status == 'complete' and errors == 0"

  # Logical operators
  - target: retry_handler
    when: "failed and (retry_count < 3 or critical == true)"

  # Function reference for complex logic
  - target: custom_validator
    when: "validators.check_output"
```

**Supported DSL features:**

- **Constants**: `true`, `false`, numbers, strings
- **Comparisons**: `==`, `!=`, `>`, `<`
- **Logical operators**: `and`/`&&`, `or`/`||`, `not`/`!`
- **Function references**: `module.function` for custom logic
- **Parentheses**: For expression grouping

## API Reference

All nodes inherit from `BaseNode` and provide:

- `.from_dict()` - Create from dictionary
- `.from_yaml_path()` - Load from YAML file
- `.compile()` - Prepare node for execution
- `.invoke()` / `.ainvoke()` - Synchronous/asynchronous execution
- `.print_spec()` - Display formatted specification
