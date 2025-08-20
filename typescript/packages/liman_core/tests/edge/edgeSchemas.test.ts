import { describe, expect, it } from "vitest";

import { EdgeSpec } from "@/edge/schemas";

describe("EdgeSpec", () => {
  it("should create edge spec with target only", () => {
    const spec = EdgeSpec.parse({ target: "target_node" });

    expect(spec.target).toBe("target_node");
    expect(spec.when).toBeUndefined();
    expect(spec.id).toBeUndefined();
    expect(spec.depends).toBeUndefined();
  });

  it("should create edge spec with when condition", () => {
    const spec = EdgeSpec.parse({ target: "target_node", when: "true" });

    expect(spec.target).toBe("target_node");
    expect(spec.when).toBe("true");
  });

  it("should create edge spec with id", () => {
    const spec = EdgeSpec.parse({ target: "target_node", id: "edge_1" });

    expect(spec.target).toBe("target_node");
    expect(spec.id).toBe("edge_1");
  });

  it("should create edge spec with dependencies", () => {
    const dependsList = ["dep1", "dep2"];
    const spec = EdgeSpec.parse({
      target: "target_node",
      depends: dependsList,
    });

    expect(spec.target).toBe("target_node");
    expect(spec.depends).toEqual(dependsList);
  });

  it("should create full edge spec", () => {
    const spec = EdgeSpec.parse({
      target: "target_node",
      when: "condition == true",
      id: "edge_1",
      depends: ["dep1", "dep2"],
    });

    expect(spec.target).toBe("target_node");
    expect(spec.when).toBe("condition == true");
    expect(spec.id).toBe("edge_1");
    expect(spec.depends).toEqual(["dep1", "dep2"]);
  });

  it("should validate edge spec from dictionary", () => {
    const specDict = {
      target: "target_node",
      when: "true",
      id: "edge_1",
      depends: ["dep1"],
    };
    const spec = EdgeSpec.parse(specDict);

    expect(spec.target).toBe("target_node");
    expect(spec.when).toBe("true");
    expect(spec.id).toBe("edge_1");
    expect(spec.depends).toEqual(["dep1"]);
  });

  it("should fail validation when target is missing", () => {
    expect(() => {
      EdgeSpec.parse({});
    }).toThrow();
  });

  it("should fail validation when target is not a string", () => {
    expect(() => {
      EdgeSpec.parse({ target: 123 });
    }).toThrow();
  });
});
