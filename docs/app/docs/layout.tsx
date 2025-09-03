import { DocsLayout, DocsLayoutProps } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { baseOptions } from "@/app/layout.config";
import { source } from "@/src/lib/source";
import { Anchor, LibraryBig } from "lucide-react";
import { SiPython } from "react-icons/si";

const docsOptions: DocsLayoutProps = {
  ...baseOptions,
  tree: source.pageTree,
  links: [],
  nav: {
    title: (
      <>
        <Anchor className="w-4 h-4" />
        Liman
      </>
    ),
  },
  sidebar: {
    tabs: [
      {
        title: "Liman AI",
        description: "Declarative AI Agent Framework",
        url: "/docs/poc",
        icon: <LibraryBig className="size-9 md:size-5 shrink-0" />,
        urls: new Set([
          "/docs/poc",
          "/docs/getting-started/simple-agent",
          "/docs/getting-started/adding-tools",
          "/docs/getting-started/openapi-integration",
          "/docs/specification/auth/service_account",
          "/docs/specification/auth/credentials_provider",
          "/docs/specification/internal_types",
          "/docs/specification/llm_node",
          "/docs/specification/node",
          "/docs/specification/overlay",
          "/docs/specification/tool_node",
          "/docs/glossary",
        ]),
      },
      {
        title: "Python SDK",
        description: "Python Reference for Liman",
        url: "/docs/python/",
        icon: <SiPython className="size-9 md:size-5 shrink-0" />,
      },
    ],
  },
};

export default function Layout({ children }: { children: ReactNode }) {
  return <DocsLayout {...docsOptions}>{children}</DocsLayout>;
}
