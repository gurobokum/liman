import { Component } from "@/base/component";
import { Plugin } from "@/plugins/core/base";
import { TBaseSpec } from "./base/schemas";

export class Registry {
  readonly #components = new Map<string, Component<TBaseSpec>>();
  readonly #pluginsKinds = new Set<string>();
  readonly #plugins = new Map<string, Plugin[]>();

  public constructor() {
    for (const kind of this.#pluginsKinds) {
      this.#plugins.set(kind, []);
    }
    console.log(this.#components);
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
}
