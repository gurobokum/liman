import type { ReactNode } from "react";
import clsx from "clsx";
import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Layout from "@theme/Layout";
import HomepageFeatures from "@site/src/components/HomepageFeatures";
import Heading from "@theme/Heading";
import { FaGithub } from "react-icons/fa";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header className="hero">
      <div className="hero-content text-center mx-auto">
        <div className="max-w-md">
          <Heading as="h1" className="text-5xl font-bold">
            {siteConfig.title}
          </Heading>
          <p>{siteConfig.tagline}</p>
          <div className="flex items-center justify-center gap-8">
            <Link className="btn btn-primary btn-lg" to="/">
              Get Started
            </Link>
            <Link
              className="link text-lg flex items-center gap-2 font-bold"
              to="https://github.com/gurobokum/liman"
            >
              <FaGithub /> <span>View on GitHub</span>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title} - Declarative AgentOps Framework`}
      description="Declarative AgentOps framework for building composable AI agents with YAML configurations"
    >
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
