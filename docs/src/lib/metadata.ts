import type { Metadata } from "next/types";

import * as links from "@/src/links";

const defaultTitle = "Liman AI";
const defaultDescription = "Declarative YAML framework for AI agents";

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
  };
}

export const baseUrl =
  process.env.NODE_ENV === "development" || !process.env.VERCEL_URL
    ? new URL("http://localhost:3000")
    : new URL(`https://${process.env.VERCEL_URL}`);
