# Liman

High-level AgentOps package for building and running conversational AI agents using YAML manifests and node-based workflows.

## Purpose

**liman** is the main entry point package that provides production-ready tools for orchestrating multi-turn AI conversations. Built on top of [liman_core](https://github.com/gurobokum/liman/tree/main/python/packages/liman_core), it offers:

- **Agent orchestration**: Manages complex conversational flows with state persistence
- **Executor engine**: Handles sequential and parallel node execution workflows
- **YAML-based configuration**: Load and compose agent definitions from declarative manifests
- **State management**: Built-in persistence for conversation history and execution state
- **Error handling**: Comprehensive logging and recovery mechanisms

## Installation

Requires Python 3.10+

```bash
# with pip
pip install liman
# with uv
uv pip install liman
# with poetry
poetry add liman
```

## Quick Start

**Step 1**: Create a directory for your agent specifications:

```bash
mkdir agents
```

**Step 2**: Create a YAML file for your agent node, e.g., `agents/llm.yaml`:

```yaml
# agents/llm.yaml
kind: LLMNode
name: assistant
description: A conversational AI assistant
prompts:
  system: You are a helpful assistant.
```

**Step 3**: Create a Python script to run the agent:

```python
from langchain_openai.chat_models import ChatOpenAI
from liman import Agent, Registry, load_specs_from_directory

llm = ChatOpenAI(model="gpt-4o")

# Create conversational agent
agent = Agent(
    "./agents",  # directory with YAML specs
    start_node="assistant"
    llm=llm,  # Langchain LLM instance
)

respones = agent.step("Hello! Can you help me with a math problem?")
print(response)
```

## Architecture

```
Agent → Executor → NodeActor → Node (from liman_core)
  ↓        ↓           ↓            ↓
Queue   Workflow   Execution   Specification
```

- **Agent**: Manages conversation queues and multi-turn interactions
- **Executor**: Orchestrates node execution with state persistence
- **State storage**: Handles conversation and execution state across sessions

## vs liman_core

| liman                      | liman_core                |
| -------------------------- | ------------------------- |
| High-level Agent class     | Low-level Node/NodeActor  |
| Multi-turn conversations   | Single node execution     |
| YAML configuration loading | Node specifications       |
| State persistence          | Stateless building blocks |
| Production error handling  | Core primitives           |

Use **liman** for building complete conversational agents, **liman_core** for low-level components that allow you to build your own orchestration.

## Development

```bash
# Run tests
poe test
# Type checking
poe mypy
# Linting
poe lint
# Format code
poe format
```
