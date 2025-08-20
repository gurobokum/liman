import fs from "fs";
import path from "path";
import vm from "vm";

import nearley from "nearley";
// @ts-expect-error - nearley internal modules don't have types
import grammar from "nearley/lib/nearley-language-bootstrapped";
// @ts-expect-error - nearley internal modules don't have types
import compile from "nearley/lib/compile";
// @ts-expect-error - nearley internal modules don't have types
import generate from "nearley/lib/generate";

import { WhenTransformer } from "./transformer";

import type { ExprNode, WhenExprNode } from "./transformer";

let compiledGrammar: nearley.Grammar | null = null;

function getCompiledGrammar(): nearley.Grammar {
  if (!compiledGrammar) {
    const grammarPath = path.resolve(__dirname, "grammar.ne");
    const grammarSource = fs.readFileSync(grammarPath, "utf8");

    const parser = new nearley.Parser(nearley.Grammar.fromCompiled(grammar));
    parser.feed(grammarSource);

    if (parser.results.length === 0)
      throw new Error("Failed to parse the grammar file.");

    const ast = parser.results[0];
    if (!ast) throw new Error("Could not parse the grammar file.");

    const compiled = compile(ast, {});
    const js = generate(compiled, "WhenGrammar");

    const context = {
      require: require,
      module: { exports: {} },
      exports: {},
    };
    vm.createContext(context);
    vm.runInContext(js, context);

    const grammarExports = context.module.exports;
    compiledGrammar = nearley.Grammar.fromCompiled(
      grammarExports as nearley.CompiledRules,
    );
    if (!compiledGrammar) throw new Error("Failed to compile the grammar.");
  }
  return compiledGrammar;
}

export class WhenParser {
  readonly #transformer = new WhenTransformer();

  public parse(input: string): WhenExprNode {
    const grammar = getCompiledGrammar();
    const parser = new nearley.Parser(grammar);

    try {
      parser.feed(input);

      if (parser.results.length === 0) {
        throw new Error(`No parse results for input: ${input}`);
      }

      if (parser.results.length > 1) {
        throw new Error(`Ambiguous parse for input: ${input}`);
      }

      const parseResult = parser.results[0];
      return this.#transformParseResult(parseResult);
    } catch (error) {
      throw new Error(`Parse error for input "${input}": ${error}`);
    }
  }

  #transformParseResult(result: unknown): WhenExprNode {
    if (typeof result === "string") {
      return this.#transformer.transformFunctionRef(result);
    }

    return this.#transformer.transformConditionalExpr(result as ExprNode);
  }
}

export const whenParser = new WhenParser();
