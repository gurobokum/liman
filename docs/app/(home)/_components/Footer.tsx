"use client";
import { Anchor, Github } from "lucide-react";
import { FaXTwitter } from "react-icons/fa6";

import * as links from "@/src/links";
import Link from "fumadocs-core/link";
import { Button } from "@/src/components/ui/button";
import Discord from "@/src/components/ui/icons/Discord";

const footerSections = [
  {
    title: "Product",
    links: [
      {
        ...links.Github,
      },
      {
        title: "Proof of Concept",
        url: "/docs/poc",
      },
    ],
  },
  {
    title: "Community",
    links: [
      {
        ...links.Discord,
      },
      {
        ...links.Twitter,
      },
      {
        ...links.RuTelegram,
      },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-fd-background border-t py-10 md:py-16">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="col-span-1 order-none">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-primary to-primary/70 rounded-lg flex items-center justify-center">
                <Anchor className="text-primary-foreground w-4 h-4" />
              </div>
              <span className="text-xl font-bold">Liman</span>
            </div>

            <p className="text-muted-foreground leading-relaxed">
              Declarative AI agent framework for building scalable intelligent
              systems.
            </p>
          </div>

          <div className="col-span-3 grid grid-cols-1 md:grid-cols-2 gap-12 md:justify-self-end">
            {footerSections.map((section) => (
              <div key={section.title}>
                <h4 className="font-bold mb-4">{section.title}</h4>
                <ul>
                  {section.links.map((link) => (
                    <li key={link.title}>
                      <Button
                        asChild={true}
                        variant="link"
                        className="text-muted-foreground p-0"
                      >
                        <Link href={link.url}>{link.title}</Link>
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-muted-foreground/20 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-foreground text-sm">
            &copy; 2025 Liman. All rights reserved.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <Link
              href={links.Github.url}
              className="text-foreground transition-colors"
            >
              <Github className="w-5 h-5" />
            </Link>
            <Link
              href={links.Twitter.url}
              className="text-foreground transition-colors"
            >
              <FaXTwitter className="w-5 h-5" />
            </Link>
            <Link href={links.Discord.url}>
              <Discord className="w-6 h-6 stroke-foreground transition-colors" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
