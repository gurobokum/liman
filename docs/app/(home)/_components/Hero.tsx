import Link from "fumadocs-core/link";
import { ArrowRight, Github, Newspaper } from "lucide-react";

import { Badge } from "@/src/components/ui/badge";
import { Button } from "@/src/components/ui/button";
import * as links from "@/src/links";

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center hero-gradient overflow-hidden">
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
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="flex flex-col items-center gap-2 mt-4 mb-8 md:mt-0 md:mb-10">
            {/*
            <Badge variant="destructive" className="animate-pulse mb-5">
              ⚠️ In Early Development Phase
            </Badge>
            */}
            <HeroBadge url="/blog/2025-08-17_simple_openapi">
              New blog post: OpenAPI integration
            </HeroBadge>
          </div>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight tracking-tight text-foreground">
            Build Reliable{" "}
            <span className="bg-gradient-to-r from-pink-500 to-pink-800 bg-clip-text text-transparent">
              AI Agents{" "}
            </span>
            with Simple YAML
          </h1>

          <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Liman is a declarative, language-agnostic framework for building AI
            agents using YAML manifests.
          </p>

          <div className="flex flex-wrap justify-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              🤖 OpenAPI → Tools Generation
            </span>
            <span className="flex items-center gap-1">
              🔐 Built-in Authorization
            </span>
            <span className="flex items-center gap-1">
              🌐 Distributed Execution
            </span>
            <span className="flex items-center gap-1">
              📊 OTel & FinOps Ready
            </span>
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button asChild size="lg" className="glow-effect group">
              <Link href="/docs/poc" external={true}>
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
              <div>Go • Java • TS</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-foreground">Graph</div>
              <div>Agent Structure</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-foreground">Kustomize</div>
              <div>Overlay System</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function HeroBadge({
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
