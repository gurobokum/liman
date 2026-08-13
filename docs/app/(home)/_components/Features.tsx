import { Card } from "@/src/components/ui/card";
import { Badge } from "@/src/components/ui/badge";
import Link from "fumadocs-core/link";
import {
  FileText,
  Cog,
  Globe,
  BarChart3,
  Layers,
  Shield,
  Network,
  Puzzle,
  GitBranch,
  Database,
  Zap,
  Pause,
} from "lucide-react";

const features = [
  {
    title: "YAML-First Manifests",
    icon: FileText,
    description:
      "Define agents as declarative YAML manifests, similar to Kubernetes. The spec is the source of truth - any language can run it.",
    badge: "YAML",
    link: "/docs/poc#yaml-manifests",
  },
  {
    title: "Dynamic Prompt Localization",
    icon: Globe,
    description:
      "Multi-language support with automatic system prompt generation. Increase function calling accuracy across languages.",
    badge: "i18n",
    link: "/docs/poc#yaml-manifests",
  },
  {
    title: "Kustomize Overlays",
    icon: Layers,
    description:
      "Layer configurations using Kustomize-like overlays. Perfect for multi-environment deployments and language variants.",
    badge: "Config",
    status: "In Development",
    link: "/docs/poc#overlays",
  },
  {
    title: "Suspension and Restoration",
    icon: Pause,
    description:
      "Fully async design - suspend or stop execution at any point and restore it from saved state. Built for multi-turn conversations and human approval gates.",
    badge: "Async",
    link: "/docs/concepts/state#state-across-restarts",
  },
  {
    title: "Lazy Initialization",
    icon: Zap,
    description:
      "Executors and actors are created only when the graph reaches them. Only the active path lives in memory, so restoring a large tree stays cheap.",
    badge: "Performance",
    link: "/docs/concepts/execution-model#lazy-initialization",
  },
  {
    title: "Condition Expression Language",
    icon: GitBranch,
    description:
      "Custom DSL for intelligent flow control between nodes. Express complex routing decisions declaratively without repetitive conditional logic.",
    badge: "Flow Control",
    link: "/docs/poc#condition-expression-language-dsl-ce",
  },
  {
    title: "Service Account Authorization",
    icon: Shield,
    description:
      "Built-in authorization with service accounts. State isolation, credential provisioning, and minimal permissions with least privilege principles.",
    badge: "Security",
    link: "/docs/poc#authentication--authorization",
  },
  {
    title: "OpenAPI → Tools Generation",
    icon: Cog,
    description:
      "Automatically generate LLM tools from OpenAPI specifications. Transform any API into agent tools without writing MCP servers.",
    badge: "Core",
    link: "/docs/poc#openapi--toolnode-generation",
  },
  {
    title: "OTel & FinOps Out-of-Box",
    icon: BarChart3,
    description:
      "Built-in OpenTelemetry integration with cost tracking. Monitor performance, token usage, and financial metrics automatically.",
    badge: "Observability",
    link: "/docs/python/liman_finops",
  },
  {
    title: "Distributed Edges",
    icon: Network,
    description:
      "Connect nodes via MCP, A2A, HTTP, WebSocket, or shared memory. Run one graph across processes, containers, and cloud functions.",
    badge: "Connectivity",
    status: "Planned",
  },
  {
    title: "Atomic State Management",
    icon: Database,
    description:
      "External state with pre_hook, invoke, post_hook phases. Persistent state survives restarts, ephemeral context lives only for the call.",
    badge: "State",
    link: "/docs/concepts/state",
  },
  {
    title: "Plugin Ecosystem",
    icon: Puzzle,
    description:
      "Extensible plugin system with built-in and custom plugins. Auto-context stitching, evaluation agents, and anomaly detection.",
    badge: "Plugins",
    status: "In Development",
    link: "/docs/poc#plugins-system",
  },
];

export default function Features() {
  return (
    <section className="py-24 bg-background text-center">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Designed for What Comes{" "}
            <span className="bg-gradient-to-r from-pink-500 to-pink-800 bg-clip-text text-transparent">
              After Hello World
            </span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            From OpenAPI tool generation to distributed execution and cost
            tracking, each feature comes from a real production pain point.
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
                  <div className="flex items-center gap-2">
                    {feature.status && (
                      <Badge
                        variant="outline"
                        className="text-xs border-dashed text-muted-foreground"
                      >
                        {feature.status}
                      </Badge>
                    )}
                    <Badge variant="secondary" className="text-xs">
                      {feature.badge}
                    </Badge>
                  </div>
                </div>
                {feature.link ? (
                  <h3 className="font-semibold mb-2 transition-colors">
                    <Link
                      href={feature.link}
                      target="_blank"
                      className="hover:text-primary hover:underline transition-colors cursor-pointer"
                    >
                      {feature.title}
                    </Link>
                  </h3>
                ) : (
                  <h3 className="font-semibold mb-2 group-hover:text-primary transition-colors">
                    {feature.title}
                  </h3>
                )}
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
