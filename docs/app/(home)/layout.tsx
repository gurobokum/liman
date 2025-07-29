import { HomeLayout } from "fumadocs-ui/layouts/home";
import type { ReactNode } from "react";

import { baseOptions } from "@/app/layout.config";
import Footer from "./_components/Footer";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <HomeLayout {...baseOptions}>
      {children}

      <Footer />
    </HomeLayout>
  );
}
