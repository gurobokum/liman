# Liman

[![](https://dcbadge.limes.pink/api/server/https://discord.gg/rmucxEzSyY?compact=true&style=flat)](https://discord.gg/rmucxEzSyY) [![Docs](https://img.shields.io/badge/docs-read-brightgreen?logo=nextdotjs)](https://liman-ai.vercel.app/docs/poc)

**Declarative AgentOps framework for building composable AI agents.**

> ⚠️ **Note:** This repository is in the early design phase.  
> It serves as a foundation for developing the Liman framework.  
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
kind: LLMNode
name: StartNode
prompts:
  system:
    en: |
      You are a helpful agent that can answer questions about the weather.
    es: |
      Eres un agente útil que puede responder preguntas sobre el clima.
  tools:
    - GetWeather

kind: ToolNode
name: GetWeather
description:
  en: Get current weather information
  es: Obtiene información actual del clima
func: mypackage.get_weather
arguments:
  - name: latitude
    type: float
    description:
      en: Latitude of the location
      es: Latitud de la ubicación
  - name: longitude
    type: float
    description:
      en: Longitude of the location
      es: Longitud de la ubicaciónk
triggers:
  en:
    - What is the weather in {latitude}, {longitude}?
    - What is the temperature in {latitude}, {longitude}?
  es:
    - ¿Cuál es el clima en {latitude}, {longitude}?
    - ¿Cuál es la temperatura en {latitude}, {longitude}?
tool_prompt_template:
  en: |
    {name} - {description}
    Examples:
      {triggers}
  es: |
    {name} - {description}
    Ejemplos:
      {triggers}
```

## Papers

- [arxiv: A Survey of AI Agent Protocols](https://arxiv.org/abs/2504.16736)
