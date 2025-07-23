import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import { Anchor } from "lucide-react";

/**
 * Shared layout configurations
 *
 * you can customise layouts individually from:
 * Home Layout: app/(home)/layout.tsx
 * Docs Layout: app/docs/layout.tsx
 */
export const baseOptions: BaseLayoutProps = {
  nav: {
    title: (
      <>
        <Anchor className="w-4 h-4" />
        Liman
      </>
    ),
  },
  // see https://fumadocs.dev/docs/ui/navigation/links
  links: [],
  githubUrl: "https://github.com/gurobokum/liman",
};
