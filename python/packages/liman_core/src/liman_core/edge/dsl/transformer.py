from lark import Token, Transformer, v_args

# Type aliases for DSL AST nodes
VarNode = tuple[str, str]  # ("var", "variable_name")
BoolNode = bool
NumberNode = float
StringNode = str
ValueNode = BoolNode | NumberNode | StringNode | VarNode

ComparisonNode = tuple[str, VarNode, ValueNode]  # ("==", var, value)
LogicalNode = tuple[str, "ExprNode", "ExprNode"]  # ("and", expr1, expr2)
NotNode = tuple[str, "ExprNode"]  # ("not", expr)
ExprNode = ValueNode | ComparisonNode | LogicalNode | NotNode

ConditionalExprNode = tuple[str, ExprNode]  # ("liman_ce", expr)
FunctionRefNode = tuple[str, str]  # ("function_ref", "module.function")
WhenExprNode = ConditionalExprNode | FunctionRefNode


@v_args(inline=True)
class WhenTransformer(Transformer[Token, WhenExprNode]):
    def conditional_expr(self, expr: ExprNode) -> ConditionalExprNode:
        return ("liman_ce", expr)

    def function_ref(self, dotted_name: str) -> FunctionRefNode:
        return ("function_ref", dotted_name)

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
        return ("var", str(name))

    def eq(self, a: VarNode, b: ValueNode) -> ComparisonNode:
        return ("==", a, b)

    def neq(self, a: VarNode, b: ValueNode) -> ComparisonNode:
        return ("!=", a, b)

    def gt(self, a: VarNode, b: ValueNode) -> ComparisonNode:
        return (">", a, b)

    def lt(self, a: VarNode, b: ValueNode) -> ComparisonNode:
        return ("<", a, b)

    def and_expr(self, a: ExprNode, b: ExprNode) -> LogicalNode:
        return ("and", a, b)

    def or_expr(self, a: ExprNode, b: ExprNode) -> LogicalNode:
        return ("or", a, b)

    def not_expr(self, a: ExprNode) -> NotNode:
        return ("not", a)
