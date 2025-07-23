import { Card } from "@/src/components/ui/card";
import { Badge } from "@/src/components/ui/badge";
import {
  FileText,
  Cog,
  Globe,
  BarChart3,
  Shield,
  Network,
  Database,
  Puzzle,
} from "lucide-react";

const features = [
  {
    icon: Cog,
    title: "OpenAPI → Tools Generation",
    description:
      "Automatically generate LLM tools from OpenAPI specifications. Transform any API into agent tools without writing MCP servers.",
    badge: "Core",
  },
  {
    icon: Shield,
    title: "Service Account Authorization",
    description:
      "Built-in authorization with service accounts and role assumption. Secure access control for distributed agent execution.",
    badge: "Security",
  },
  {
    icon: Globe,
    title: "Dynamic Prompt Localization",
    description:
      "Multi-language support with automatic system prompt generation. Increase function calling accuracy across languages.",
    badge: "i18n",
  },
  {
    icon: BarChart3,
    title: "OTel & FinOps Out-of-Box",
    description:
      "Built-in OpenTelemetry integration with cost tracking. Monitor performance, token usage, and financial metrics automatically.",
    badge: "Observability",
  },
  {
    icon: Network,
    title: "Distributed Edges",
    description:
      "Connect nodes via MCP, A2A, HTTP, WebSocket, or shared memory. Build distributed agents across AWS Lambda and processes.",
    badge: "Connectivity",
  },
  {
    icon: Database,
    title: "Atomic State Management",
    description:
      "External state with pre_hook, invoke, post_hook phases. Build complex distributed agents with flexible state handling.",
    badge: "State",
  },
  {
    icon: Puzzle,
    title: "Plugin Ecosystem",
    description:
      "Extensible plugin system with built-in and custom plugins. Auto-context stitching, evaluation agents, and anomaly detection.",
    badge: "Plugins",
  },
  {
    icon: FileText,
    title: "Kustomize Overlays",
    description:
      "Layer configurations using Kustomize-like overlays. Perfect for multi-environment deployments and language variants.",
    badge: "Config",
  },
];

export default function Features() {
  return (
    <section className="py-24 bg-background text-center">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Built for{" "}
            <span className="bg-gradient-to-r from-primary to-primary-glow bg-clip-text text-transparent">
              AgentOps
            </span>{" "}
            at Scale
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            From OpenAPI integration to distributed execution, Liman provides
            everything needed to build, deploy, and operate production AI agents
            across multiple languages and environments.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card
                key={index}
                className="p-6 border-animated glow-effect hover:shadow-lg transition-all duration-300 group"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {feature.badge}
                  </Badge>
                </div>
                <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
