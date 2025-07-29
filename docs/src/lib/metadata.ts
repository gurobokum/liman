import type { Metadata } from "next/types";

import * as links from "@/src/links";

export function createMetadata(metdata: Metadata): Metadata {
  return {
    ...metdata,
    openGraph: {
      title: metdata.title ?? undefined,
      description: metdata.description ?? undefined,
      url: links.Liman.url,
      siteName: links.Liman.title,
      ...metdata.openGraph,
    },
    twitter: {
      card: "summary_large_image",
      creator: "@liman_ai",
      title: metdata.title ?? undefined,
      description: metdata.description ?? undefined,
      ...metdata.twitter,
    },
  };
}

export const baseUrl =
  process.env.NODE_ENV === "development" || !process.env.VERCEL_URL
    ? new URL("http://localhost:3000")
    : new URL(`https://${process.env.VERCEL_URL}`);
