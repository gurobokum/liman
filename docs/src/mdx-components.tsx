import defaultMdxComponents from "fumadocs-ui/mdx";
import type { MDXComponents } from "mdx/types";
import * as PythonMDX from "fumadocs-python/components";

import ASCIinema from "./components/asciinema";
import { Mermaid } from "./components/mdx/Mermaid";
import { Accordion, Accordions } from "fumadocs-ui/components/accordion";
import { MemeIcon } from "./components/ui/meme";

// use this function to get MDX components, you will need it for rendering MDX
export function getMDXComponents(components?: MDXComponents): MDXComponents {
  return {
    ...defaultMdxComponents,
    ASCIinema,
    Accordion,
    Accordions,
    Mermaid,
    MemeIcon,
    ...PythonMDX,
    ...components,
  };
}
