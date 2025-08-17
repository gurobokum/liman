import { HomeLayout } from "fumadocs-ui/layouts/home";
import type { ReactNode } from "react";

import { baseOptions } from "@/app/layout.config";
import Footer from "./_components/Footer";
import { createMetadata } from "@/src/lib/metadata";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <HomeLayout {...baseOptions}>
      {children}

      <Footer />
    </HomeLayout>
  );
}

export async function generateMetadata() {
  return createMetadata({});
}
