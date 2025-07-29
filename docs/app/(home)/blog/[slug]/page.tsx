import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { InlineTOC } from "fumadocs-ui/components/inline-toc";
import { Github } from "lucide-react";
import { FaXTwitter, FaLinkedin } from "react-icons/fa6";
import path from "node:path";

import { blog } from "@/src/lib/source";
import { createMetadata } from "@/src/lib/metadata";
import { buttonVariants } from "@/src/components/ui/button";

import { Control } from "./_components/controls";

export default async function Page(props: {
  params: Promise<{ slug: string }>;
}) {
  const params = await props.params;
  const page = blog.getPage([params.slug]);

  if (!page) notFound();
  const { body: Mdx, toc } = await page.data.load();

  return (
    <>
      <div className="relative container rounded-xl mt-12 py-12 md:px-8 overflow-hidden bg-gray-50 dark:bg-slate-950">
        {/* Dark theme gradients */}
        <div className="absolute bottom-0 left-[-20%] right-0 top-[-10%] h-[500px] w-[500px] rounded-full dark:block hidden bg-[radial-gradient(circle_farthest-side,rgba(255,0,182,.15),rgba(255,255,255,0))]"></div>
        <div className="absolute bottom-0 right-[-20%] top-[-10%] h-[500px] w-[500px] rounded-full dark:block hidden bg-[radial-gradient(circle_farthest-side,rgba(255,0,182,.15),rgba(255,255,255,0))]"></div>

        {/* Light theme gradients */}
        <div className="absolute bottom-0 left-[-20%] right-0 top-[-10%] h-[500px] w-[500px] rounded-full dark:hidden block bg-[radial-gradient(circle_farthest-side,rgba(236,72,153,.08),rgba(255,255,255,0))]"></div>
        <div className="absolute bottom-0 right-[-20%] top-[-10%] h-[500px] w-[500px] rounded-full dark:hidden block bg-[radial-gradient(circle_farthest-side,rgba(236,72,153,.08),rgba(255,255,255,0))]"></div>

        <div className="relative z-10">
          <h1 className="mb-2 text-3xl font-bold text-foreground">
            {page.data.title}
          </h1>
          <p className="mb-4 text-muted-foreground">{page.data.description}</p>
          <Link
            href="/blog"
            className={buttonVariants({ size: "sm", variant: "outline" })}
          >
            Back
          </Link>
        </div>
      </div>
      <article className="container flex flex-col px-0 py-8 lg:flex-row lg:px-4">
        <div className="prose min-w-0 flex-1 p-4">
          <InlineTOC items={toc} />
          <Mdx />
        </div>
        <div className="flex flex-col gap-4 border-l p-4 text-sm lg:w-[250px]">
          <div>
            <p className="mb-1 text-fd-muted-foreground">Written by</p>
            <div className="flex items-center gap-3">
              {page.data.authorGravatarUrl && (
                <Image
                  width={256}
                  height={256}
                  src={page.data.authorGravatarUrl}
                  alt={page.data.author}
                  className="w-8 h-8 rounded-full flex-shrink-0"
                />
              )}
              <div className="flex-1">
                <p className="font-medium">{page.data.author}</p>
                {(page.data.authorTwitterUrl ||
                  page.data.authorGithubUrl ||
                  page.data.authorLinkedInUrl) && (
                  <div className="flex gap-2 mt-1">
                    {page.data.authorTwitterUrl && (
                      <Link
                        href={page.data.authorTwitterUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-fd-muted-foreground hover:text-primary transition-colors"
                      >
                        <FaXTwitter className="w-4 h-4" />
                      </Link>
                    )}
                    {page.data.authorGithubUrl && (
                      <Link
                        href={page.data.authorGithubUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-fd-muted-foreground hover:text-primary transition-colors"
                      >
                        <Github className="w-4 h-4" />
                      </Link>
                    )}
                    {page.data.authorLinkedInUrl && (
                      <Link
                        href={page.data.authorLinkedInUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-fd-muted-foreground hover:text-primary transition-colors"
                      >
                        <FaLinkedin className="w-4 h-4" />
                      </Link>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div>
            <p className="mb-1 text-sm text-fd-muted-foreground">At</p>
            <p className="font-medium">
              {new Date(
                page.data.date ??
                  path.basename(page.path, path.extname(page.path)),
              ).toDateString()}
            </p>
          </div>
          <Control url={page.url} />
        </div>
      </article>
    </>
  );
}

export async function generateMetadata(props: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const params = await props.params;
  const page = blog.getPage([params.slug]);

  if (!page) notFound();

  return createMetadata({
    title: page.data.title,
    description:
      page.data.description ?? "Liman AI Agents Blog - Insights and Updates",
  });
}

export function generateStaticParams(): { slug: string }[] {
  return blog.getPages().map((page) => ({
    slug: page.slugs[0],
  }));
}
