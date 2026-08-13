import Link from "next/link";
import Image from "next/image";

import { blog } from "@/src/lib/source";

type BlogPost = ReturnType<typeof blog.getPages>[number];

export function BlogPostCardView({ post }: { post: BlogPost }) {
  return (
    <Link
      href={post.url}
      className="group relative overflow-hidden rounded-lg border bg-card p-6 transition-all duration-300 no-underline"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />

      <div className="relative z-10">
        <h3 className="mb-3 text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
          {post.data.title}
        </h3>
        <p className="text-sm text-muted-foreground leading-relaxed mb-4">
          {post.data.description}
        </p>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {post.data.authorGravatarUrl && (
              <Image
                width={256}
                height={256}
                src={post.data.authorGravatarUrl}
                alt={post.data.author}
                className="w-6 h-6 rounded-full border border-border"
              />
            )}
            <span className="text-xs text-muted-foreground font-medium">
              {post.data.author}
            </span>
          </div>

          <time className="text-xs text-muted-foreground font-medium">
            {new Date(post.data.date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
        </div>
      </div>
    </Link>
  );
}

export function BlogPosts({
  limit,
  order = "desc",
}: {
  limit?: number;
  order?: "asc" | "desc";
}) {
  const posts = [...blog.getPages()].sort((a, b) => {
    const diff =
      new Date(b.data.date).getTime() - new Date(a.data.date).getTime();
    return order === "desc" ? diff : -diff;
  });
  const shown = limit ? posts.slice(0, limit) : posts;

  return (
    <div className="not-prose mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
      {shown.map((post) => (
        <BlogPostCardView key={post.url} post={post} />
      ))}
    </div>
  );
}
