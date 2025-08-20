export type VarNode = {
  readonly type: "var";
  readonly name: string;
};

export type BoolNode = boolean;
export type NumberNode = number;
export type StringNode = string;
export type ValueNode = BoolNode | NumberNode | StringNode | VarNode;

export type ComparisonNode = {
  readonly type: "==" | "!=" | ">" | "<";
  readonly left: ValueNode;
  readonly right: ValueNode;
};

export type LogicalNode = {
  readonly type: "and" | "or" | "&&" | "||";
  readonly left: ExprNode;
  readonly right: ExprNode;
};

export type NotNode = {
  readonly type: "not";
  readonly expr: ExprNode;
};

export type ExprNode = ComparisonNode | LogicalNode | NotNode | ValueNode;

export enum ExprType {
  LIMAN_CE = "liman_ce",
  FUNCTION_REF = "function_ref",
}

export type ConditionalExprNode = {
  readonly type: ExprType.LIMAN_CE;
  readonly expr: ExprNode;
};

export type FunctionRefNode = {
  readonly type: ExprType.FUNCTION_REF;
  readonly dottedName: string;
};

export type WhenExprNode = ConditionalExprNode | FunctionRefNode;

export class WhenTransformer {
  public transformConditionalExpr(expr: ExprNode): ConditionalExprNode {
    return { type: ExprType.LIMAN_CE, expr };
  }

  public transformFunctionRef(dottedName: string): FunctionRefNode {
    return { type: ExprType.FUNCTION_REF, dottedName };
  }
}
