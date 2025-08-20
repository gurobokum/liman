# Nearley grammar for when expressions
#
@{%
const moo = require('moo');

const lexer = moo.compile({
  WS: /[ \t]+/,
  TRUE: 'true',
  FALSE: 'false',
  AND: ['&&', 'and'],
  OR: ['||', 'or'],
  EQ: '==',
  NEQ: '!=',
  NOT: ['!', 'not'],
  GT: '>',
  LT: '<',
  NUMBER: /-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?/,
  STRING: [/"(?:[^"\\]|\\.)*"/, /'(?:[^'\\]|\\.)*'/],
  NAME: /[a-zA-Z_]\w*/,
  LPAREN: '(',
  RPAREN: ')',
  DOT: '.',
});

lexer.next = (next => () => {
  let tok;
  while ((tok = next.call(lexer)) && tok.type === "WS") {}
  return tok;
})(lexer.next);
%}

@lexer lexer

start -> when_expr {% id %}

when_expr -> conditional_expr {% id %}
           | function_ref {% id %}

conditional_expr -> expr {% id %}

expr -> or_expr {% id %}

or_expr -> and_expr %OR or_expr {% d => ({type: 'or', left: d[0], right: d[2]}) %}
         | and_expr {% id %}

and_expr -> not_expr %AND and_expr {% d => ({type: 'and', left: d[0], right: d[2]}) %}
          | not_expr {% id %}

not_expr -> %NOT not_expr {% d => ({type: 'not', expr: d[1]}) %}
          | atom {% id %}

atom -> comparison {% id %}
      | %LPAREN expr %RPAREN {% d => d[1] %}

comparison -> var %EQ var {% d => ({type: '==', left: d[0], right: d[2]}) %}
            | var %EQ value {% d => ({type: '==', left: d[0], right: d[2]}) %}
            | value %EQ var {% d => ({type: '==', left: d[0], right: d[2]}) %}
            | value %EQ value {% d => ({type: '==', left: d[0], right: d[2]}) %}
            | var %NEQ var {% d => ({type: '!=', left: d[0], right: d[2]}) %}
            | var %NEQ value {% d => ({type: '!=', left: d[0], right: d[2]}) %}
            | value %NEQ var {% d => ({type: '!=', left: d[0], right: d[2]}) %}
            | value %NEQ value {% d => ({type: '!=', left: d[0], right: d[2]}) %}
            | var %GT var {% d => ({type: '>', left: d[0], right: d[2]}) %}
            | var %GT value {% d => ({type: '>', left: d[0], right: d[2]}) %}
            | value %GT var {% d => ({type: '>', left: d[0], right: d[2]}) %}
            | value %GT value {% d => ({type: '>', left: d[0], right: d[2]}) %}
            | var %LT var {% d => ({type: '<', left: d[0], right: d[2]}) %}
            | var %LT value {% d => ({type: '<', left: d[0], right: d[2]}) %}
            | value %LT var {% d => ({type: '<', left: d[0], right: d[2]}) %}
            | value %LT value {% d => ({type: '<', left: d[0], right: d[2]}) %}
            | var {% id %}
            | value {% id %}

var -> %NAME {% d => ({type: 'var', name: d[0].value}) %}

value -> %TRUE {% () => true %}
       | %FALSE {% () => false %}
       | %STRING {% d => d[0].value.slice(1, -1) %}
       | %NUMBER {% d => parseFloat(d[0].value) %}

function_ref -> dotted_name {% id %}

dotted_name -> %NAME (%DOT %NAME):+ {% d => d[0].value + d[1].map(x => '.' + x[1].value).join('') %}
