# Liman

### [Proof of Concept](https://www.liman-ai.dev/docs/poc)

[![Docs](https://img.shields.io/badge/docs-read-brightgreen?logo=nextdotjs)](https://liman-ai.vercel.app/docs/poc)
[![Discord](https://dcbadge.limes.pink/api/server/https://discord.gg/rmucxEzSyY?compact=true&style=flat)](https://discord.gg/rmucxEzSyY) [![X Follow](https://img.shields.io/twitter/follow/liman_ai?style=social)](https://x.com/liman_ai)

Declarative framework for building composable AI agents using YAML manifests and node-based architecture.

> ⚠️ **Warning:** This project is in active development and not ready for production use.

## Features

- **Declarative YAML Configuration**: Define agents using simple YAML manifests
- **Multi-language Support**: Built-in localization for prompts and descriptions
- **Node-based Architecture**: Compose workflows from LLM, Tool, and custom nodes
- **Edge DSL**: Connect nodes with conditional expressions and function references
- **OpenAPI Integration**: Auto-generate tools from OpenAPI specifications
- **Built-in Observability**: OpenTelemetry support with FinOps tracking
- **Multi-runtime**: Python implementation (Go planned)

## Architecture

Liman represents AI agents as graphs of interconnected nodes, similar to Kubernetes manifests with Kustomize-style overlays:

- **LLMNode**: Wraps LLM requests with system prompts and tool integration
- **ToolNode**: Defines function calls for LLM tool integration
- **Node**: Custom logic nodes for complex workflows
- **Edges**: Connect nodes with conditional execution using custom DSL

## Example

```yaml
kind: LLMNode
name: assistant
prompts:
  system:
    en: You are a helpful assistant.
    es: Eres un asistente útil.
tools:
  - calculator
nodes:
  - target: analyzer
    when: result == "success"
---
kind: ToolNode
name: calculator
description:
  en: Performs mathematical calculations
func: my_module.calculate
arguments:
  - name: expression
    type: str
    description:
      en: Mathematical expression to evaluate
---
kind: Node
name: analyzer
func: my_module.analyze
```

## Python

### Packages

- [**liman_core**](python/packages/liman_core): Core library with node types and YAML processing
- [**liman_finops**](python/packages/liman_finops): OpenTelemetry instrumentation and cost tracking
- [**liman_openapi**](python/packages/liman_openapi): OpenAPI to ToolNode generation

## Resources

- [📖 Documentation](https://liman-ai.vercel.app/docs/poc)
- [🔧 Specification](https://liman-ai.vercel.app/docs/specification/node)
