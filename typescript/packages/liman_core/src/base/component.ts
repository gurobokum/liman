import fs from "fs/promises";

import { highlight } from "cli-highlight";
import { isPlainObject } from "es-toolkit";
import yaml, { Document } from "yaml";
import { z } from "zod";

import { InvalidSpecError } from "@/errors";
import { Registry } from "@/registry";

import { BaseSpec, TBaseSpec } from "./schemas";

export type ComponentConstructorOptions = {
  readonly initialData?: Readonly<{ [key: string]: unknown }>;
  readonly yamlPath?: string;
  readonly strict?: boolean;
};

export type ConstructorParams = [
  registry: Registry,
  options?: ComponentConstructorOptions,
];

export type ComponentConstructor<
  S extends TBaseSpec,
  R extends Component<S>,
> = (new (spec: S, ...args: ConstructorParams) => R) & {
  readonly specType: z.ZodType<TBaseSpec>;

  fromDict: (
    this: ComponentConstructor<S, R>,
    data: Readonly<{ [key: string]: unknown }>,
    registry: Registry,
    options?: ComponentConstructorOptions,
  ) => R;
  fromYamlPath: (
    this: ComponentConstructor<S, R>,
    yamlPath: string,
    registry: Registry,
    options?: ComponentConstructorOptions,
  ) => Promise<R>;
};

export abstract class Component<S extends TBaseSpec> {
  public readonly spec: S;
  public static readonly specType: z.ZodType<TBaseSpec> = BaseSpec;

  public readonly id: string;
  public readonly name: string;
  public readonly strict: boolean;
  public readonly yamlPath?: string;
  public readonly registry: Registry;

  protected readonly _initialData?: Readonly<{ [key: string]: unknown }>;

  public constructor(spec: S, ...args: ConstructorParams) {
    const [registry, options = {}] = args;
    const { initialData, yamlPath, strict = false } = options;

    this.spec = spec;

    this._initialData = initialData;
    this.yamlPath = yamlPath;
    this.strict = strict;
    this.registry = registry;

    this.id = this.generateId();
    this.name = this.spec.name;
  }

  public toString(): string {
    return `${this.spec.kind}:${this.name}`;
  }

  public static fromDict<S extends TBaseSpec, R extends Component<S>>(
    this: ComponentConstructor<S, R>,
    data: Readonly<{ [key: string]: unknown }>,
    registry: Registry,
    options: ComponentConstructorOptions = {},
  ): R {
    const spec = this.specType.parse(data) as S;

    return new this(spec, registry, {
      ...options,
      initialData: data,
    });
  }

  public static async fromYamlPath<S extends TBaseSpec, R extends Component<S>>(
    this: ComponentConstructor<S, R>,
    yamlPath: string,
    registry: Registry,
    options: ComponentConstructorOptions = {},
  ): Promise<R> {
    const yamlData = await fs.readFile(yamlPath, "utf-8");
    const data = yaml.parse(yamlData);

    if (!isPlainObject(data)) {
      throw new InvalidSpecError(
        "YAML content must be a dictionary at the top level.",
      );
    }

    return this.fromDict(data, registry, {
      ...options,
      yamlPath,
    });
  }

  public generateId(): string {
    return crypto.randomUUID();
  }

  public get fullName(): string {
    return `${this.spec.kind}/${this.name}`;
  }

  public printSpec(initial: boolean = false): void {
    const data = initial ? this._initialData : this.spec;
    const yamlOutput = highlightYaml(data);
    console.log(yamlOutput);
  }
}

type YamlValue =
  | Readonly<{ [key: string]: unknown }>
  | readonly YamlValue[]
  | string
  | null;

export function highlightYaml(data?: YamlValue): string {
  if (!data) return "";

  const doc = new Document(data);
  const yamlString = doc
    .toString({
      indent: 4,
      lineWidth: 0,
      blockQuote: false,
      minContentWidth: 0,
    })
    .trim();

  return highlight(yamlString, {
    language: "yaml",
    theme: "monokai",
  });
}
