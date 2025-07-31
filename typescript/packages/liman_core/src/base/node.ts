import { z } from "zod";

export type LanguageCode = string;

export const BaseSpecSchema = z.object({
  kind: z.string(),
  name: z.string(),
});

export type BaseSpec = z.infer<typeof BaseSpecSchema>;

export type NodeConstructorOptions = {
  readonly initialData?: Readonly<{ [key: string]: unknown }>;
  readonly yamlPath?: string;
  readonly strict?: boolean;
  readonly defaultLang?: string;
  readonly fallbackLang?: string;
};

export type BaseMessage = {
  content: string;
  role: string;
};

export class Output<S extends BaseSpec> {
  public readonly response: BaseMessage;
  public readonly nextNodes: readonly (readonly [
    BaseNode<S>,
    Readonly<{ [key: string]: unknown }>,
  ])[];

  public constructor(
    response: BaseMessage,
    nextNodes: readonly (readonly [
      BaseNode<S>,
      Readonly<{ [key: string]: unknown }>,
    ])[] = [],
  ) {
    this.response = response;
    this.nextNodes = nextNodes;
  }
}

export abstract class BaseNode<S extends BaseSpec> {
  public readonly id: string;
  public readonly name: string;
  public readonly strict: boolean;
  public readonly spec: S;
  public readonly yamlPath?: string;
  public readonly defaultLang: LanguageCode;
  public readonly fallbackLang: LanguageCode;

  protected readonly _initialData?: Readonly<{ [key: string]: unknown }>;
  protected _compiled: boolean = false;

  public constructor(spec: S, options: NodeConstructorOptions = {}) {
    const {
      initialData,
      yamlPath,
      strict = false,
      defaultLang = "en",
      fallbackLang = "en",
    } = options;

    if (!this.#isValidLanguageCode(defaultLang)) {
      throw new Error(`Invalid default language code: ${defaultLang}`);
    }
    this.defaultLang = defaultLang;

    if (!this.#isValidLanguageCode(fallbackLang)) {
      throw new Error(`Invalid fallback language code: ${fallbackLang}`);
    }
    this.fallbackLang = fallbackLang;

    this._initialData = initialData;
    this.spec = spec;
    this.yamlPath = yamlPath;

    this.id = this.generateId();
    this.name = this.spec.name;

    this.strict = strict;
    this._compiled = false;
  }

  public toString(): string {
    return `${this.spec.kind}:${this.name}`;
  }

  public static fromDict<T extends BaseNode<BaseSpec>>(
    this: new (spec: BaseSpec, options?: NodeConstructorOptions) => T,
    _data: Readonly<{ [key: string]: unknown }>,
  ): T {
    throw new Error("fromDict must be implemented by subclasses");
  }

  public static fromYamlPath<T extends BaseNode<BaseSpec>>(
    this: new (spec: BaseSpec, options?: NodeConstructorOptions) => T,
    _yamlPath: string,
  ): T {
    throw new Error("fromYamlPath must be implemented by subclasses");
  }

  public generateId(): string {
    return crypto.randomUUID();
  }

  public abstract compile(): void;

  public abstract invoke(
    ...args: readonly unknown[]
  ): Output<S> | Promise<Output<S>>;

  public abstract ainvoke(...args: readonly unknown[]): Promise<Output<S>>;

  public get isLlmNode(): boolean {
    return this.spec.kind === "LLMNode";
  }

  public get isToolNode(): boolean {
    return this.spec.kind === "ToolNode";
  }

  public printSpec(initial: boolean = false): void {
    const data = initial ? this._initialData : this.spec;
    console.log(JSON.stringify(data, null, 2));
  }

  #isValidLanguageCode(code: string): boolean {
    return /^[a-z]{2}(-[A-Z]{2})?$/.test(code);
  }
}

export type YamlValue =
  | Readonly<{ [key: string]: unknown }>
  | readonly YamlValue[]
  | string
  | null;

export function preserveMultilineStrings(data: YamlValue): YamlValue {
  if (data === null || data === undefined) {
    return null;
  }

  if (typeof data === "string" && data.includes("\n")) {
    return data;
  }

  if (typeof data === "object" && !Array.isArray(data)) {
    const result: { [key: string]: unknown } = {};
    for (const [key, value] of Object.entries(data)) {
      result[key] = preserveMultilineStrings(value as YamlValue);
    }
    return result;
  }

  if (Array.isArray(data)) {
    return data
      .map((item: YamlValue) => preserveMultilineStrings(item))
      .filter((item: YamlValue) => item !== null);
  }
  return data;
}
