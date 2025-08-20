import { describe, it, expect, vi } from "vitest";

import { Component } from "@/base/component";
import { Registry } from "@/registry";
import { TBaseSpec } from "@/base/schemas";

class TestComponent extends Component<TBaseSpec> {}

describe("Component", () => {
  const testSpec: TBaseSpec = { kind: "TestComponent", name: "test-component" };
  const registry = new Registry();

  it("should create component with spec", () => {
    const component = new TestComponent(testSpec, registry);

    expect(component.name).toBe("test-component");
    expect(component.spec.kind).toBe("TestComponent");
    expect(component.strict).toBe(false);
    expect(component.yamlPath).toBeUndefined();
    expect(component.registry).toBe(registry);
  });

  it("should create component with options", () => {
    const initialData = { custom: "data" };
    const yamlPath = "/path/to/file.yaml";
    const component = new TestComponent(testSpec, registry, {
      initialData,
      yamlPath,
      strict: true,
    });

    expect(component.strict).toBe(true);
    expect(component.yamlPath).toBe(yamlPath);
  });

  it("should generate unique id", () => {
    const component1 = new TestComponent(testSpec, registry);
    const component2 = new TestComponent(testSpec, registry);

    expect(component1.id).not.toBe(component2.id);
    expect(component1.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
    );
  });

  it("should return correct string representation", () => {
    const component = new TestComponent(testSpec, registry);
    expect(component.toString()).toBe("TestComponent:test-component");
  });

  it("should have fullName property", () => {
    const component = new TestComponent(testSpec, registry);
    expect(component.fullName).toBe("TestComponent/test-component");
  });

  it("should print spec correctly", () => {
    const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    const component = new TestComponent(testSpec, registry);

    const expectedSpec = "kind: TestComponent\nname: test-component";

    component.printSpec();
    expect(consoleSpy).toHaveBeenCalledWith(expectedSpec);

    component.printSpec(true);
    expect(consoleSpy).toHaveBeenCalledWith(expectedSpec);

    consoleSpy.mockRestore();
  });

  it("should implement fromDict in subclass", () => {
    const data = { kind: "TestComponent", name: "from-dict" };
    const component = TestComponent.fromDict(data, registry);

    expect(component.name).toBe("from-dict");
    expect(component.spec.kind).toBe("TestComponent");
  });
});
