import Link from "fumadocs-core/link";
import {
  ArrowRight,
  Github,
  Newspaper,
  Cog,
  Shield,
  Pause,
  BarChart3,
} from "lucide-react";

import { Button } from "@/src/components/ui/button";
import * as links from "@/src/links";

export default function Hero() {
  return (
    <section className="relative py-32 md:py-48 hero-gradient overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary-glow/5" />
      <div className="absolute inset-0 bg-[url('/api/placeholder/1920/1080')] opacity-5 bg-cover bg-center" />

      {/* Floating elements */}
      <div
        className="absolute top-20 left-10 w-20 h-20 rounded-full bg-primary/10 blur-xl float-animation"
        style={{ animationDelay: "0s" }}
      />
      <div
        className="absolute top-40 right-20 w-32 h-32 rounded-full bg-primary-glow/10 blur-xl float-animation"
        style={{ animationDelay: "1s" }}
      />
      <div
        className="absolute bottom-40 left-20 w-24 h-24 rounded-full bg-primary/10 blur-xl float-animation"
        style={{ animationDelay: "2s" }}
      />

      <div className="container mx-auto px-4 text-center relative z-10">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* announcement badge - restore when a new post is ready
          <div className="flex flex-col items-center gap-2 mt-4 mb-8 md:mt-0 md:mb-10">
            <HeroBadge url="/blog/2025-08-17_simple_openapi">
              New blog post: OpenAPI integration
            </HeroBadge>
          </div>
          */}
          <h1 className="text-5xl md:text-8xl mb-16 font-bold leading-none tracking-tight text-foreground">
            AI Agents as{" "}
            <span className="bg-gradient-to-r from-pink-500 to-pink-800 bg-clip-text text-transparent">
              Manifests
            </span>
            <span className="block text-2xl md:text-3xl font-normal text-muted-foreground mt-8">
              Define the Graph. Any Language Runs It.
            </span>
          </h1>

          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
            <span className="flex items-center gap-2">
              <Cog className="w-4 h-4" />
              OpenAPI → Tools Generation
            </span>
            <span className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Built-in Authorization
            </span>
            <span className="flex items-center gap-2">
              <Pause className="w-4 h-4" />
              Suspend & Resume Execution
            </span>
            <span className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              OTel & FinOps Ready
            </span>
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button asChild size="lg" className="glow-effect group">
              <Link href="/docs/getting-started/simple-agent" external={true}>
                Get Started
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="border-animated glow-effect"
            >
              <Link href={links.Github.url}>
                <Github className="w-4 h-4 mr-2" />
                View on GitHub
              </Link>
            </Button>
          </div>

          <div className="flex justify-center gap-8 text-sm text-muted-foreground pt-8">
            <div className="text-center">
              <div className="font-semibold text-foreground">Python</div>
              <div>Available now</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-foreground">Graph</div>
              <div>Compose any flow</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-foreground">Overlays</div>
              <div>Extend without forking</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function HeroBadge({
  children,
  url,
}: {
  children?: React.ReactNode;
  url: string;
}) {
  return (
    <span className="relative inline-block overflow-hidden rounded-full p-[1px]">
      <span className="news-badge-glow"></span>
      <div className="inline-flex h-full w-full cursor-pointer justify-center rounded-full bg-white px-3 py-1 text-xs font-medium leading-5 text-slate-600 backdrop-blur-xl dark:bg-black dark:text-slate-200">
        <Link href={url} className="flex items-center gap-2" target="_blank">
          <Newspaper className="w-3 h-3" />
          {children}
        </Link>
      </div>
    </span>
  );
}
