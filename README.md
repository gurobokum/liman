# Liman (WIP)

**Declarative AgentOps framework for building composable AI agents.**

> ⚠️ **Note:** This repository is in the early design phase.  
> It serves as a foundation for developing the Liman framework.  
> **No functional features have been implemented yet.**  
> Follow the repo to stay updated as development progresses!

- [ ] **🧠 Declarative agent design** — define agents, tools, workflows via simple YAML.
- [ ] **📊 Built-in observability** — OpenTelemetry support out of the box.
- [ ] **🌐 OpenAPI parsing** — generate agents automatically from OpenAPI specifications.
- [ ] **🔁 Multi-runtime** — Python & Go support for execution.
- [ ] **🧱 Composable architecture** — modular nodes and chains like LangGraph.

## Design philosophy

Liman is similar to Kubernetes manifests and Kustomize-style overlays:

- Define your agents declaratively, just like Kubernetes manifests.
- Layer configurations with overlays to adapt agents to different environments and languages.
- Compose reusable building blocks — tools, LLMs, workflows — in a modular, pluggable way.

## Declaration

```yaml
name: MyAgent
lang: en
main:
  system:
    intro: |
      You are a helpful agent that can answer questions about the weather.
    tool_template: |
      * {tool_function} - {tool_description}
        Possible triggers: {tool_triggers}
  tools:
    - name: get_weather
      description: Get current weather information
      arguments:
        - name: latitude
          type: float
          description: Latitude of the location
        - name: longitude
          type: float
          description: Longitude of the location
      triggers:
        - What is the weather in {latitude}, {longitude}?
        - What is the temperature in {latitude}, {longitude}?
```
