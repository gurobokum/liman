import Link from "next/link";
import { Anchor } from "lucide-react";
import Image from "next/image";

import { blog } from "@/src/lib/source";

export default function Page(): React.ReactElement {
  const posts = [...blog.getPages()].sort(
    (a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime(),
  );

  return (
    <main className="md:container md:px-8 md:py-12">
      <div className="relative h-[300px] md:h-[400px] flex items-center justify-center overflow-hidden md:rounded-lg md:border md:mx-0">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-primary-glow/5" />
        <div className="absolute inset-0 bg-[url('/api/placeholder/1920/1080')] opacity-5 bg-cover bg-center" />

        {/* Floating elements */}
        <div
          className="absolute top-20 left-10 w-20 h-20 rounded-full bg-primary/10 blur-xl float-animation"
          style={{ animationDelay: "0s" }}
        />
        <div
          className="absolute top-40 right-20 w-32 h-32 rounded-full bg-primary-glow/10 blur-xl float-animation"
          style={{ animationDelay: "1s" }}
        />
        <div
          className="absolute bottom-40 left-20 w-24 h-24 rounded-full bg-primary/10 blur-xl float-animation"
          style={{ animationDelay: "2s" }}
        />

        <div className="container mx-auto px-4 text-center relative z-10">
          <div className="max-w-4xl mx-auto space-y-8">
            <h1 className="text-4xl md:text-6xl font-bold leading-tight tracking-tight text-foreground">
              <Link
                href="/blog"
                className="hover:opacity-80 transition-opacity flex items-center justify-center gap-4"
              >
                <Anchor className="w-8 h-8 md:w-12 md:h-12 text-primary" />
                Liman{" "}
                <span className="bg-gradient-to-r from-pink-500 to-pink-800 bg-clip-text text-transparent">
                  Blog
                </span>
              </Link>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Updates, insights, and best practices for building reliable AI
              agents with Liman.
            </p>
          </div>
        </div>
      </div>
      <div className="mt-12 mb-24 px-4 md:px-0 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => (
          <Link
            key={post.url}
            href={post.url}
            className="group relative overflow-hidden rounded-lg border bg-card p-6 transition-all duration-300"
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
        ))}
      </div>
    </main>
  );
}
