import { describe, it, expect } from "vitest";

import { BaseSpec, TBaseSpec } from "@/base/schemas";

describe("BaseSpecSchema", () => {
  it("should validate valid spec", () => {
    const validSpec = { kind: "TestNode", name: "test" };
    const result = BaseSpec.parse(validSpec);

    expect(result.kind).toBe("TestNode");
    expect(result.name).toBe("test");
  });

  it("should reject spec without kind", () => {
    const invalidSpec = { name: "test" };

    expect(() => BaseSpec.parse(invalidSpec)).toThrow();
  });

  it("should reject spec without name", () => {
    const invalidSpec = { kind: "TestNode" };

    expect(() => BaseSpec.parse(invalidSpec)).toThrow();
  });

  it("should reject spec with non-string kind", () => {
    const invalidSpec = { kind: 123, name: "test" };

    expect(() => BaseSpec.parse(invalidSpec)).toThrow();
  });

  it("should reject spec with non-string name", () => {
    const invalidSpec = { kind: "TestNode", name: 123 };

    expect(() => BaseSpec.parse(invalidSpec)).toThrow();
  });

  it("should allow additional properties", () => {
    const specWithExtra = {
      kind: "TestNode",
      name: "test",
      extra: "property",
    };

    const result = BaseSpec.parse(specWithExtra);
    expect(result.kind).toBe("TestNode");
    expect(result.name).toBe("test");
  });
});

describe("BaseSpec type", () => {
  it("should have correct type structure", () => {
    const spec: TBaseSpec = { kind: "TestNode", name: "test" };

    expect(typeof spec.kind).toBe("string");
    expect(typeof spec.name).toBe("string");
  });
});
