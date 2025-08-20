# Liman

Code-first declarative framework for building composable AI agents using YAML manifests

> ⚠️ **Warning:** This project is in early development phase.

## Features

- **Declarative YAML Configuration**: Define agents using simple YAML manifests
- **Node-based Architecture**: Compose workflows from LLM, Tool, and custom nodes
- **Edge DSL**: Connect nodes with conditional expressions and function references
- **OpenAPI Integration**: Auto-generate tools from OpenAPI specifications
- **Multi-language Support**: Built-in localization for prompts and descriptions
- **Built-in Observability**: OpenTelemetry support with FinOps tracking
- **Multi-runtime**: Python implementation (TS, Go planned)

## Quick Start (python)

```bash
pip install liman
```

Create agent specifications in YAML:

```yaml
# agents/assistant.yaml
kind: LLMNode
name: assistant
description: A conversational AI assistant
prompts:
  system: You are a helpful assistant that can check weather.
tools:
  - get_weather
```

```yaml
# agents/get_weather_tool.yaml
kind: ToolNode
name: get_weather
description:
  en: Get current weather information for a city
func: weather.get_current_weather
arguments:
  - name: city
    type: str
    description:
      en: Name of the city to get weather for
```

Create a Python function for the tool:

```python
# weather.py
def get_current_weather(city: str) -> str:
    """Get weather information for a city."""
    # Your weather API logic here
    return f"The weather in {city} is sunny, 22°C"
```

Run the agent:

```python
# main.py
from langchain_openai.chat_models import ChatOpenAI
from liman import Agent

llm = ChatOpenAI(model="gpt-4o")

agent = Agent(
    "./agents",  # directory with YAML specs
    start_node="assistant",
    llm=llm
)

response = agent.step("What's the weather like in London?")
print(response)
```

## Architecture

Liman represents AI agents as graphs of interconnected nodes, similar to Kubernetes manifests with Kustomize-style overlays:

- **LLMNode**: Wraps LLM requests with system prompts and tool integration
- **ToolNode**: Defines function calls for LLM tool integration
- **FunctionNode**: Custom logic nodes for complex workflows
- **Edges**: Connect nodes with conditional execution using custom DSL

## Edge DSL

Liman includes a custom Domain Specific Language (DSL) that defines the logic of executing agents through conditional expressions in node edges. The DSL supports:

### Examples

```yaml
nodes:
  # Simple condition
  - target: success_handler
    when: status == 'complete'

  # Complex logical expression
  - target: retry_handler
    when: (status == 'failed' && retry_count < 3) || priority == 'high'

  # Function reference
  - target: custom_handler
    when: utils.should_process
```

The DSL expressions are parsed at runtime and evaluated against the current execution context.

## Python

### Packages

- [**liman**](python/packages/liman): Main package with executor and agent functionality, should be used as an entry point [![codecov](https://codecov.io/gh/gurobokum/liman/graph/badge.svg?token=PMKWXNBF1K&component=python/liman)](https://codecov.io/gh/gurobokum/liman?components[0]=python/liman)
- [**liman_core**](python/packages/liman_core): Core library with node types and YAML processing [![codecov](https://codecov.io/gh/gurobokum/liman/graph/badge.svg?token=PMKWXNBF1K&component=python/liman_core)](https://codecov.io/gh/gurobokum/liman?components[0]=python/liman_core)
- [**liman_finops**](python/packages/liman_finops): OpenTelemetry instrumentation and cost tracking.
- [**liman_openapi**](python/packages/liman_openapi): OpenAPI to ToolNode generation [![codecov](https://codecov.io/gh/gurobokum/liman/graph/badge.svg?token=PMKWXNBF1K&component=python/liman_openapi)](https://codecov.io/gh/gurobokum/liman?components[0]=python/liman_openapi)

## Resources

- [📖 Documentation](https://liman-ai.vercel.app/docs/poc)
- [🔧 Specification](https://liman-ai.vercel.app/docs/specification/node)

[![Docs](https://img.shields.io/badge/docs-read-brightgreen?logo=nextdotjs)](https://liman-ai.vercel.app/docs/poc)
[![Discord](https://dcbadge.limes.pink/api/server/https://discord.gg/rmucxEzSyY?compact=true&style=flat)](https://discord.gg/rmucxEzSyY) [![X Follow](https://img.shields.io/twitter/follow/liman_ai?style=social)](https://x.com/liman_ai)
