"use client";

import Link from "fumadocs-core/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/src/components/ui/button";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/src/components/ui/tabs";
import { cn } from "@/src/lib/utils";

type Tab = {
  label: string;
  yamlLabel: string;
  yamlHtml: string;
  extraYamlLabel?: string;
  extraYamlHtml?: string;
  pythonLabel: string;
  pythonHtml: string;
  ctaHref: string;
  ctaLabel: string;
  ctaIcon: React.ReactNode;
};

const BADGE = "TypeScript SDK coming soon";

export default function CodeTabs({ tabs }: { tabs: Tab[] }) {
  return (
    <Tabs defaultValue={tabs[0].label}>
      <div className="flex justify-center mb-6">
        <TabsList>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.label} value={tab.label}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>

      {tabs.map((tab) => (
        <TabsContent key={tab.label} value={tab.label}>
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left column */}
            <div className="flex flex-col gap-4 min-w-0">
              <div
                className={cn(
                  !tab.extraYamlHtml && "flex flex-col flex-1 min-h-0",
                )}
              >
                <div className="text-sm font-medium text-muted-foreground mb-2">
                  {tab.yamlLabel}
                </div>
                <div
                  className={cn(
                    "rounded-lg overflow-auto text-sm [&>pre]:p-4 [&>pre]:rounded-lg",
                    !tab.extraYamlHtml && "flex-1 min-h-0 [&>pre]:h-full",
                  )}
                  dangerouslySetInnerHTML={{ __html: tab.yamlHtml }}
                />
              </div>
              {tab.extraYamlHtml && (
                <div className="flex flex-col flex-1 min-h-0">
                  <div className="text-sm font-medium text-muted-foreground mb-2">
                    {tab.extraYamlLabel}
                  </div>
                  <div className="rounded-lg overflow-hidden flex-1 min-h-0 max-h-56">
                    <div
                      className="overflow-auto text-sm h-full [&>pre]:p-4 [&>pre]:rounded-none [&>pre]:min-h-full"
                      dangerouslySetInnerHTML={{ __html: tab.extraYamlHtml }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Right column */}
            <div className="flex flex-col min-w-0">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">
                  {tab.pythonLabel}
                </span>
                <span className="text-xs bg-primary/10 text-primary rounded-full px-2 py-0.5 font-medium">
                  {BADGE}
                </span>
              </div>
              <div
                className="rounded-lg overflow-auto text-sm flex-1 min-h-0 [&>pre]:p-4 [&>pre]:rounded-lg [&>pre]:h-full"
                dangerouslySetInnerHTML={{ __html: tab.pythonHtml }}
              />
            </div>
          </div>

          <div className="flex justify-center mt-12">
            <Button
              asChild
              variant="outline"
              size="lg"
              className="border-animated glow-effect group"
            >
              <Link href={tab.ctaHref}>
                {tab.ctaIcon}
                {tab.ctaLabel}
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Link>
            </Button>
          </div>
        </TabsContent>
      ))}
    </Tabs>
  );
}
