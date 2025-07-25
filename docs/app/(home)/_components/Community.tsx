"use client";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, Github } from "lucide-react";

import { Button } from "@/src/components/ui/button";
import { Card } from "@/src/components/ui/card";
import Discord from "@/src/components/ui/icons/Discord";
import Link from "fumadocs-core/link";

import * as links from "@/src/links";

const communityLinks = [
  {
    icon: Github,
    title: links.Github.title,
    url: links.Github.url,
    description:
      "Contribute to the code, report issues, and join discussions with the community",
    buttonText: "View Repository",
    color:
      "bg-slate-100 hover:bg-slate-200 group-hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 dark:group-hover:bg-slate-700",
  },
  {
    icon: Discord,
    title: links.Discord.title,
    url: links.Discord.url,
    description:
      "Chat with developers in real-time and get help from the community",
    buttonText: "Join Discord",
    color:
      "bg-indigo-100 hover:bg-indigo-200 group-hover:bg-indigo-200 dark:bg-indigo-900 dark:hover:bg-indigo-800 dark:group-hover:bg-indigo-800",
  },
  {
    icon: BookOpen,
    title: "Documentation",
    url: "/docs/poc",
    description: "Explore comprehensive API documentation and usage examples",
    buttonText: "Read Docs",
    color:
      "bg-emerald-100 hover:bg-emerald-200 group-hover:bg-emerald-200 dark:bg-emerald-900 dark:hover:bg-emerald-800 dark:group-hover:bg-emerald-800",
  },
];

export default function Community() {
  return (
    <section id="community" className="py-20 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Join the Community
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            Participate in specification development and share experiences with
            other developers
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8">
          {communityLinks.map((link, index) => {
            const Icon = link.icon;

            return (
              <motion.div
                key={link.title}
                className="text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                whileHover={{ y: -5 }}
              >
                <Card className="p-8 group">
                  <div
                    className={`w-16 h-16 ${link.color} rounded-xl flex items-center justify-center mx-auto mb-6 transition-colors`}
                  >
                    <Icon className="text-foreground w-8 h-8 stroke-foreground" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-4">
                    {link.title}
                  </h3>
                  <p className="text-muted-foreground mb-6 leading-relaxed">
                    {link.description}
                  </p>
                  <Button variant="ghost" asChild={true}>
                    <Link href={link.url}>
                      {link.buttonText}
                      <ArrowRight className="ml-1 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </Link>
                  </Button>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
