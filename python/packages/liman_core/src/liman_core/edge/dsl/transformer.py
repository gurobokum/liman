from enum import Enum
from typing import Literal, NamedTuple

from lark import Token, Transformer, v_args


# Type aliases for DSL AST nodes
# ("var", "variable_name")
class VarNode(NamedTuple):
    type_: Literal["var"]
    name: str


BoolNode = bool
NumberNode = float
StringNode = str
ValueNode = BoolNode | NumberNode | StringNode | VarNode


# ("==", operand, operand) - both sides can be variables or values
class ComparisonNode(NamedTuple):
    type_: Literal["==", "!=", ">", "<"]
    left: ValueNode
    right: ValueNode


# ("and", expr1, expr2)
class LogicalNode(NamedTuple):
    type_: Literal["and", "or", "&&", "||"]
    left: "ExprNode"
    right: "ExprNode"


# ("not", expr)
class NotNode(NamedTuple):
    type_: Literal["not"]
    expr: "ExprNode"


ExprNode = ComparisonNode | LogicalNode | NotNode | ValueNode


class ExprType(str, Enum):
    LIMAN_CE = "liman_ce"
    FUNCTION_REF = "function_ref"


class ConditionalExprNode(NamedTuple):
    type_: Literal[ExprType.LIMAN_CE]
    expr: ExprNode


class FunctionRefNode(NamedTuple):
    type_: Literal[ExprType.FUNCTION_REF]
    dotted_name: str


WhenExprNode = ConditionalExprNode | FunctionRefNode


@v_args(inline=True)
class WhenTransformer(Transformer[Token, WhenExprNode]):
    def conditional_expr(self, expr: ExprNode) -> ConditionalExprNode:
        return ConditionalExprNode(ExprType.LIMAN_CE, expr)

    def function_ref(self, dotted_name: str) -> FunctionRefNode:
        return FunctionRefNode(ExprType.FUNCTION_REF, dotted_name)

    def dotted_name(self, *names: Token) -> str:
        return ".".join(str(name) for name in names)

    def string_literal(self, s: Token) -> Token:
        return s

    def true(self) -> BoolNode:
        return True

    def false(self) -> BoolNode:
        return False

    def number(self, n: Token) -> NumberNode:
        return float(n)

    def string(self, s: str | Token) -> StringNode:
        if isinstance(s, str):
            return s[1:-1]  # remove quotes
        return str(s)[1:-1]  # handle Token objects

    def var(self, name: Token) -> VarNode:
        return VarNode("var", str(name))

    def eq(self, a: ValueNode, b: ValueNode) -> ComparisonNode:
        return ComparisonNode("==", a, b)

    def neq(self, a: ValueNode, b: ValueNode) -> ComparisonNode:
        return ComparisonNode("!=", a, b)

    def gt(self, a: ValueNode, b: ValueNode) -> ComparisonNode:
        return ComparisonNode(">", a, b)

    def lt(self, a: ValueNode, b: ValueNode) -> ComparisonNode:
        return ComparisonNode("<", a, b)

    def and_expr(self, a: ExprNode, b: ExprNode) -> LogicalNode:
        return LogicalNode("and", a, b)

    def or_expr(self, a: ExprNode, b: ExprNode) -> LogicalNode:
        return LogicalNode("or", a, b)

    def not_expr(self, a: ExprNode) -> NotNode:
        return NotNode("not", a)
