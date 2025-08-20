import { describe, expect, it } from "vitest";

import { whenParser } from "@/edge/dsl/grammar";
import { ExprType } from "@/edge/dsl/transformer";

describe("WhenDSL", () => {
  it("should parse simple string with single quotes", () => {
    const result = whenParser.parse("status == 'active'");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "==",
        left: { type: "var", name: "status" },
        right: "active",
      },
    });
  });

  it("should parse simple string with double quotes", () => {
    const result = whenParser.parse('name == "John Doe"');
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "==",
        left: { type: "var", name: "name" },
        right: "John Doe",
      },
    });
  });

  it("should parse simple true", () => {
    const result = whenParser.parse("true");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: true,
    });
  });

  it("should parse simple false", () => {
    const result = whenParser.parse("false");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: false,
    });
  });

  it("should parse simple equality", () => {
    const result = whenParser.parse("value == 42");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "==",
        left: { type: "var", name: "value" },
        right: 42,
      },
    });
  });

  it("should parse simple inequality", () => {
    const result = whenParser.parse("value != 42");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "!=",
        left: { type: "var", name: "value" },
        right: 42,
      },
    });
  });

  it("should parse simple greater than", () => {
    const result = whenParser.parse("value > 42");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: ">",
        left: { type: "var", name: "value" },
        right: 42,
      },
    });
  });

  it("should parse simple less than", () => {
    const result = whenParser.parse("value < 42");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "<",
        left: { type: "var", name: "value" },
        right: 42,
      },
    });
  });

  it("should parse complex and expression", () => {
    const result = whenParser.parse("status == 'active' && count > 5");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "and",
        left: {
          type: "==",
          left: { type: "var", name: "status" },
          right: "active",
        },
        right: {
          type: ">",
          left: { type: "var", name: "count" },
          right: 5,
        },
      },
    });
  });

  it("should parse complex or expression", () => {
    const result = whenParser.parse("status == 'inactive' || count < 10");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "or",
        left: {
          type: "==",
          left: { type: "var", name: "status" },
          right: "inactive",
        },
        right: {
          type: "<",
          left: { type: "var", name: "count" },
          right: 10,
        },
      },
    });
  });

  it("should parse complex not expression", () => {
    const result = whenParser.parse("!(status == 'disabled')");
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "not",
        expr: {
          type: "==",
          left: { type: "var", name: "status" },
          right: "disabled",
        },
      },
    });
  });

  it("should parse parentheses in expressions", () => {
    const result = whenParser.parse(
      "(status == 'active' && count > 5) || priority == 'high'",
    );
    expect(result).toEqual({
      type: ExprType.LIMAN_CE,
      expr: {
        type: "or",
        left: {
          type: "and",
          left: {
            type: "==",
            left: { type: "var", name: "status" },
            right: "active",
          },
          right: {
            type: ">",
            left: { type: "var", name: "count" },
            right: 5,
          },
        },
        right: {
          type: "==",
          left: { type: "var", name: "priority" },
          right: "high",
        },
      },
    });
  });

  it("should parse simple function reference", () => {
    const result = whenParser.parse("utils.check_status");
    expect(result).toEqual({
      type: ExprType.FUNCTION_REF,
      dottedName: "utils.check_status",
    });
  });

  it("should parse dotted function reference", () => {
    const result = whenParser.parse("my_app.utils.validators.check_status");
    expect(result).toEqual({
      type: ExprType.FUNCTION_REF,
      dottedName: "my_app.utils.validators.check_status",
    });
  });
});
