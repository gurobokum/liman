import { DocsLayout, DocsLayoutProps } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { baseOptions } from "@/app/layout.config";
import { source } from "@/src/lib/source";
import { GithubInfo } from "fumadocs-ui/components/github-info";
import { Anchor } from "lucide-react";

const docsOptions: DocsLayoutProps = {
  ...baseOptions,
  tree: source.pageTree,
  links: [
    {
      type: "custom",
      children: <GithubInfo owner="gurobokum" repo="liman" />,
    },
  ],
  nav: {
    title: (
      <>
        <Anchor className="w-4 h-4" />
        Liman
      </>
    ),
  },
};

export default function Layout({ children }: { children: ReactNode }) {
  return <DocsLayout {...docsOptions}>{children}</DocsLayout>;
}
