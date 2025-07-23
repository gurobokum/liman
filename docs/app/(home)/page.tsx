import { Toaster } from "@/src/components/ui/sonner";

import Community from "./_components/Community";
import Features from "./_components/Features";
import Footer from "./_components/Footer";
import GettingStarted from "./_components/GettingStarted";
import Hero from "./_components/Hero";
import Subscribe from "./_components/Subscribe";

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col justify-center">
      <Hero />
      <Features />
      <GettingStarted />
      <Subscribe />
      <Community />
      <Footer />
      <Toaster />
    </main>
  );
}
