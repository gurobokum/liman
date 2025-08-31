import { Component } from "@/base/component";
import { LimanError } from "@/errors";
import { Plugin } from "@/plugins/core/base";
import { TBaseSpec } from "./base/schemas";

export class Registry {
  readonly #components = new Map<string, Component<TBaseSpec>>();
  readonly #pluginsKinds = new Set<string>(["Node", "LLMNode", "ToolNode"]);
  readonly #plugins = new Map<string, Plugin[]>();

  public constructor() {
    for (const kind of this.#pluginsKinds) {
      this.#plugins.set(kind, []);
    }
  }

  public getPlugins(kind: string): readonly Plugin[] {
    return this.#plugins.get(kind) ?? [];
  }

  public addPlugins(plugins: readonly Plugin[]): void {
    for (const plugin of plugins) {
      for (const kind of plugin.registeredKinds) {
        if (this.#pluginsKinds.has(kind)) {
          throw new Error(`Kind is already registered: ${kind}`);
        }
        const existing = this.#plugins.get(kind) ?? [];
        this.#plugins.set(kind, [...existing, plugin]);
      }

      for (const appliedKind of plugin.appliesTo) {
        if (!this.#pluginsKinds.has(appliedKind)) {
          throw new Error(`Applied kind is not supported: ${appliedKind}`);
        }
        const existing = this.#plugins.get(appliedKind) ?? [];
        this.#plugins.set(appliedKind, [...existing, plugin]);
      }
    }
  }

  public lookup<T extends Component<TBaseSpec>>(
    kind: new (...args: unknown[]) => T,
    name: string,
  ): T {
    const key = `${kind.name}:${name}`;
    const component = this.#components.get(key);

    if (!component) {
      throw new LimanError(`Component with key '${key}' not found in registry`);
    }

    if (!(component instanceof kind)) {
      throw new TypeError(
        `Retrieved component '${component.name}' is of type ${component.constructor.name}, but expected type ${kind.name}`,
      );
    }

    return component as T;
  }

  public add(component: Component<TBaseSpec>): void {
    const key = `${component.spec.kind}:${component.name}`;

    if (this.#components.has(key)) {
      throw new LimanError(
        `Component with key '${key}' already exists in registry`,
      );
    }

    this.#components.set(key, component);
  }

  public get(name: string): Component<TBaseSpec> | undefined {
    return this.#components.get(name);
  }
}
