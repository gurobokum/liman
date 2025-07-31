import { describe, it, expect } from "vitest";
import { BaseSpecSchema } from "./node";

describe("BaseSpecSchema", () => {
  it("should validate valid spec", () => {
    const validSpec = { kind: "TestNode", name: "test" };
    expect(() => BaseSpecSchema.parse(validSpec)).not.toThrow();
  });
});
