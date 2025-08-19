import type { Metadata } from "next/types";

import * as links from "@/src/links";

const defaultTitle = "Liman AI";
const defaultDescription = "Declarative YAML framework for AI agents";

export const baseUrl =
  process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000";

export function createMetadata(metdata: Metadata): Metadata {
  return {
    ...metdata,
    openGraph: {
      title: metdata.title ?? defaultTitle,
      description: metdata.description ?? defaultDescription,
      url: links.Liman.url,
      siteName: links.Liman.title,
      images: "/og.png",
      ...metdata.openGraph,
    },
    twitter: {
      card: "summary_large_image",
      creator: "@liman_ai",
      title: metdata.title ?? defaultTitle,
      description: metdata.description ?? defaultDescription,
      ...metdata.twitter,
    },

    alternates: {
      types: {
        "application/rss+xml": [
          {
            title: "LimanAI Blog",
            url: `${baseUrl}/rss.xml`,
          },
        ],
      },
    },
  };
}
