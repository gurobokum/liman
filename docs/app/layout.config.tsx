import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";
import { AlbumIcon, Anchor, Book } from "lucide-react";

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
  links: [
    {
      text: "Docs",
      url: "/docs/poc",
      icon: <Book />,
      active: "nested-url",
    },
    {
      text: "Blog",
      url: "/blog",
      icon: <AlbumIcon />,
      active: "nested-url",
    },
  ],
  githubUrl: "https://github.com/gurobokum/liman",
};
