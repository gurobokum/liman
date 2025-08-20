import { LimanError } from "@/errors";
import { isValidLanguageCode, LanguageCode } from "@/languages";
import { TNodeState } from "@/nodes/base/schemas";
import { Registry } from "@/registry";

import { Component, ComponentConstructorOptions } from "./component";
import { TBaseSpec } from "./schemas";

export type NodeConstructorOptions = ComponentConstructorOptions & {
  readonly defaultLang?: LanguageCode;
  readonly fallbackLang?: LanguageCode;
};

export abstract class BaseNode<
  S extends TBaseSpec,
  NS extends TNodeState,
> extends Component<S> {
  public readonly defaultLang: LanguageCode;
  public readonly fallbackLang: LanguageCode;

  protected _compiled: boolean = false;

  public constructor(
    spec: S,
    registry: Registry,
    options: NodeConstructorOptions = {},
  ) {
    const {
      defaultLang = "en",
      fallbackLang = "en",
      ...componentOptions
    } = options;

    super(spec, registry, componentOptions);

    if (!isValidLanguageCode(defaultLang)) {
      throw new LimanError(`Invalid default language code: ${defaultLang}`);
    }
    this.defaultLang = defaultLang;

    if (!isValidLanguageCode(fallbackLang)) {
      throw new LimanError(`Invalid fallback language code: ${fallbackLang}`);
    }
    this.fallbackLang = fallbackLang;

    this._compiled = false;
  }

  public toString(): string {
    return `${this.spec.kind}:${this.name}`;
  }

  public generateId(): string {
    return crypto.randomUUID();
  }

  public abstract compile(): void;

  public abstract invoke(...args: unknown[]): Promise<unknown>;

  public abstract getNewState(): NS;
}

export type YamlValue =
  | Readonly<{ [key: string]: unknown }>
  | readonly YamlValue[]
  | string
  | null;
