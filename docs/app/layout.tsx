import { RootProvider } from "fumadocs-ui/provider";
import { Inter } from "next/font/google";
import React from "react";

import "@/app/global.css";
import Analytics from "@/src/components/Analytics";

const inter = Inter({
  subsets: ["latin"],
});

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider>{children}</RootProvider>
        <Analytics />
      </body>
    </html>
  );
}
