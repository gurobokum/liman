import { codeToHtml } from "shiki";
import { BookOpen, Newspaper, Wrench } from "lucide-react";

import CodeTabs from "./CodeTabs";

const simpleYaml = `kind: LLMNode
name: assistant
prompts:
  system:
    en: |
      You are a helpful assistant.
      Always be polite and provide clear answers.`;

const simplePython = `from liman import Agent
from langchain_openai import ChatOpenAI

agent = Agent(
    "./specs",
    start_node="assistant",
    llm=ChatOpenAI(model="gpt-5.4-mini"),
)

response = await agent.step("Hello!")
print(response)`;

const toolsLLMYaml = `kind: LLMNode
name: assistant
tools:
  - get_user_by_name
prompts:
  system:
    en: |
      You are a helpful assistant.
      Always be polite and provide clear answers.`;

const toolsToolYaml = `kind: ToolNode
name: get_user_by_name
description: Find a specific user by their name
func: main.get_user_by_name
arguments:
  - name: user_name
    type: string
    description: The name of the user to find`;

const toolsPython = `from liman import Agent
from langchain_openai import ChatOpenAI

def get_user_by_name(user_name: str) -> str:
    users = {
        "Alice": "alice@example.com",
        "Bob": "bob@example.com",
    }
    email = users.get(user_name)
    if email:
        return f"{user_name}: {email}"
    return f"User '{user_name}' not found"

agent = Agent(
    "./specs",
    start_node="assistant",
    llm=ChatOpenAI(model="gpt-5.4-mini"),
)

response = await agent.step("Find user Alice")
print(response)`;

const openapiYaml = `kind: LLMNode
name: assistant
tools:
  - OpenAPI__get_user
prompts:
  system:
    en: |
      You are a user management assistant.`;

const openapiSpecYaml = `openapi: "3.0.0"
info:
  title: User Management API
  version: 1.0.0
paths:
  /users/{user_name}:
    get:
      operationId: get_user
      summary: Get a user by name
      parameters:
        - name: user_name
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: User found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/User"
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        email:
          type: string
`;

const openapiPython = `from liman import Agent
from liman_openapi import (
    load_openapi,
    create_tool_nodes,
)
from langchain_openai import ChatOpenAI

spec = load_openapi("./openapi.yaml")
tools = create_tool_nodes(spec, prefix="OpenAPI")

agent = Agent(
    "./specs",
    start_node="assistant",
    llm=ChatOpenAI(model="gpt-5.4-mini"),
    extra_nodes=tools,
)

response = await agent.step("Find user Alice")
print(response)`;

export default async function CodeExample() {
  const theme = "github-dark";

  const [
    simpleYamlHtml,
    simplePythonHtml,
    toolsLLMYamlHtml,
    toolsToolYamlHtml,
    toolsPythonHtml,
    openapiYamlHtml,
    openapiSpecYamlHtml,
    openapiPythonHtml,
  ] = await Promise.all([
    codeToHtml(simpleYaml, { lang: "yaml", theme }),
    codeToHtml(simplePython, { lang: "python", theme }),
    codeToHtml(toolsLLMYaml, { lang: "yaml", theme }),
    codeToHtml(toolsToolYaml, { lang: "yaml", theme }),
    codeToHtml(toolsPython, { lang: "python", theme }),
    codeToHtml(openapiYaml, { lang: "yaml", theme }),
    codeToHtml(openapiSpecYaml, { lang: "yaml", theme }),
    codeToHtml(openapiPython, { lang: "python", theme }),
  ]);

  const tabs = [
    {
      label: "Simple Agent",
      yamlLabel: "specs/assistant.yaml",
      yamlHtml: simpleYamlHtml,
      pythonLabel: "main.py",
      pythonHtml: simplePythonHtml,
      ctaHref: "/docs/getting-started/simple-agent",
      ctaLabel: "Build your first agent step by step",
      ctaIcon: <BookOpen className="w-4 h-4 mr-2 text-chart-2" />,
    },
    {
      label: "With Tools",
      yamlLabel: "specs/assistant.yaml",
      yamlHtml: toolsLLMYamlHtml,
      extraYamlLabel: "specs/tool.yaml",
      extraYamlHtml: toolsToolYamlHtml,
      pythonLabel: "main.py",
      pythonHtml: toolsPythonHtml,
      ctaHref: "/docs/getting-started/adding-tools",
      ctaLabel: "Learn how to add custom tools",
      ctaIcon: <Wrench className="w-4 h-4 mr-2 text-chart-2" />,
    },
    {
      label: "OpenAPI",
      yamlLabel: "specs/assistant.yaml",
      yamlHtml: openapiYamlHtml,
      extraYamlLabel: "openapi.yaml",
      extraYamlHtml: openapiSpecYamlHtml,
      pythonLabel: "main.py",
      pythonHtml: openapiPythonHtml,
      ctaHref: "/blog/2025-08-17_simple_openapi",
      ctaLabel: "Read the OpenAPI integration post",
      ctaIcon: <Newspaper className="w-4 h-4 mr-2 text-chart-2" />,
    },
  ];

  return (
    <section className="py-24 bg-muted/30">
      <div className="container mx-auto px-4 max-w-5xl">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            See How It Works
          </h2>
          <p className="text-xl text-muted-foreground">
            Define your agent in YAML. Run it with the SDK.
          </p>
        </div>

        <CodeTabs tabs={tabs} />
      </div>
    </section>
  );
}
