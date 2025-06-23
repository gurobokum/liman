# Liman Core

Core AgentOps library

## Spec

- [x] - optional
- <x> - user input

### LLMNode

```yaml
kind: LLMNode
name: <name>
prompts:
  system:
    [lang]: |
      <system prompt>
tools:
  - <ToolNode>
```

### ToolNode

```yaml
kind: ToolNode
name: <name>
description:
  [lang]: |
    <description>
func: <function name with import path>
arguments:
  - name: <argument name>
    type: <argument type>
    description:
      [lang]: |
        <argument description>
```
