# Nearley grammar for when expressions
#
@{%
const moo = require('moo');

const lexer = moo.compile({
  WS: /[ \t]+/,
  NAME: /[a-zA-Z_]\w*/,
  NUMBER: /-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?/,
  STRING: [/"(?:[^"\\]|\\.)*"/, /'(?:[^'\\]|\\.)*'/],
  EQ: '==',
  NEQ: '!=',
  GT: '>',
  LT: '<',
  AND: ['&&', 'and'],
  OR: ['||', 'or'],
  NOT: ['!', 'not'],
  TRUE: 'true',
  FALSE: 'false',
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

start -> or_expr {% id %}

or_expr -> or_expr %OR and_expr {% d => ({type: 'or', left: d[0], right: d[2]}) %}
         | and_expr {% id %}

and_expr -> and_expr %AND not_expr {% d => ({type: 'and', left: d[0], right: d[2]}) %}
          | not_expr {% id %}

not_expr -> %NOT atom {% d => ({type: 'not', expr: d[1]}) %}
          | atom {% id %}

atom -> primary %EQ primary {% d => ({type: '==', left: d[0], right: d[2]}) %}
      | primary %NEQ primary {% d => ({type: '!=', left: d[0], right: d[2]}) %}
      | primary %GT primary {% d => ({type: '>', left: d[0], right: d[2]}) %}
      | primary %LT primary {% d => ({type: '<', left: d[0], right: d[2]}) %}
      | primary {% id %}

primary -> %LPAREN or_expr %RPAREN {% d => d[1] %}
         | dotted_name {% d => d[0].includes('.') ? d[0] : {type: 'var', name: d[0]} %}
         | %TRUE {% () => true %}
         | %FALSE {% () => false %}
         | %STRING {% d => d[0].value.slice(1, -1) %}
         | %NUMBER {% d => parseFloat(d[0].value) %}

dotted_name -> %NAME (%DOT %NAME):* {% d => d[0].value + d[1].map(x => '.' + x[1].value).join('') %}
