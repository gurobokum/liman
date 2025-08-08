from lark import Lark

when_grammar = r"""
    ?start: when_expr

    ?when_expr: conditional_expr
              | function_ref

    conditional_expr: expr

    ?expr: expr "&&" expr   -> and_expr
         | expr "and" expr  -> and_expr
         | expr "||" expr   -> or_expr
         | expr "or" expr   -> or_expr
         | "!" expr         -> not_expr
         | "not" expr       -> not_expr
         | operand "==" operand   -> eq
         | operand "!=" operand   -> neq
         | operand ">" operand    -> gt
         | operand "<" operand    -> lt
         | "(" expr ")"
         | var
         | value

    ?operand: var | value

    ?var: NAME              -> var

    ?value: "true"          -> true
          | "false"         -> false
          | string_literal  -> string
          | SIGNED_NUMBER   -> number

    ?string_literal: ESCAPED_STRING
                   | SINGLE_QUOTED_STRING

    function_ref: dotted_name

    ?dotted_name: NAME ("." NAME)+

    SINGLE_QUOTED_STRING: /'([^'\\\\]|\\\\.)*'/

    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.CNAME -> NAME
    %import common.WS
    %ignore WS
"""

when_parser = Lark(when_grammar, start="start", parser="lalr")
