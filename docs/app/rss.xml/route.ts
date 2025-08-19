import { Feed } from "feed";
import { blog } from "@/src/lib/source";
import { NextResponse } from "next/server";
import { baseUrl } from "@/src/lib/metadata";

export const revalidate = false;

export function GET() {
  console.log(baseUrl);
  const feed = new Feed({
    title: "LimanAI Blog",
    id: `${baseUrl}/blog`,
    link: `${baseUrl}/blog`,
    language: "en",

    image: `${baseUrl}/og.png`,
    favicon: `${baseUrl}/icon.png`,
    copyright: "All rights reserved 2025, LimanAI",
  });

  for (const page of blog.getPages().sort((a, b) => {
    return new Date(b.data.date).getTime() - new Date(a.data.date).getTime();
  })) {
    feed.addItem({
      id: page.url,
      title: page.data.title,
      description: page.data.description,
      link: `${baseUrl}${page.url}`,
      date: new Date(page.data.date),

      author: [
        {
          name: "Guro Bokum",
          email: "jiojiajiu@gmail.com",
        },
      ],
    });
  }

  return new NextResponse(feed.rss2());
}
