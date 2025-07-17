import type { BaseLayoutProps } from "fumadocs-ui/layouts/shared";

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
        <svg
          width="24"
          height="24"
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
          aria-label="Logo"
        >
          <path
            d="M 20 30 C 20 60, 70 60, 70 30 L 70 80 C 70 90, 20 90, 20 80 Z"
            stroke="var(--color-fd-primary)"
            stroke-width="5"
            fill="none"
          />

          <path
            d="M 70 45 C 85 45, 85 65, 70 65"
            stroke="var(--color-fd-primary)"
            stroke-width="5"
            fill="none"
          />

          <path
            d="M 45 28 Q 50 15, 60 10 C 55 15, 50 25, 45 28 Z"
            stroke="var(--color-fd-primary)"
            stroke-width="4"
            fill="none"
          />

          <path
            d="M 40 10 Q 45 -3, 55 -8 C 50 -3, 45 7, 40 10 Z"
            stroke="var(--color-fd-primary)"
            stroke-width="5"
            fill="none"
          />
        </svg>
        Liman
      </>
    ),
  },
  // see https://fumadocs.dev/docs/ui/navigation/links
  links: [],
  githubUrl: "https://github.com/gurobokum/liman",
};
