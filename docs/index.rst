
.. _index:

====================
Hermes documentation
====================

.. rubric:: LL(1) recursive descent parser generator with expression support and abstract syntax tree translation.  Hermes can generate parsers in Python, Java, C, and JavaScript.  Alternatively, Hermes can be used as a Python module:

test.gr

.. code-block:: hast

    (JsonObject:
      values=[
        (KeyValue:
          key=<string (line 1 col 2) `"a"`>,
          value=<integer (line 1 col 7) `1`>
        ),
        (KeyValue:
          key=<string (line 1 col 10) `"b"`>,
          value=(JsonList:
            values=[
              <integer (line 1 col 16) `2`>,
              <integer (line 1 col 18) `3`>
            ]
          )
        )
      ]
    )

.. code-block:: htree

    (json:
      (obj:
        <lbrace (line 1 col 1) `{`>,
        (_gen0:
          (key_value_pair:
            (key:
              <string (line 1 col 2) `"a"`>
            ),
            <colon (line 1 col 5) `:`>,
            (value:
              <integer (line 1 col 7) `1`>
            )
          ),
          (_gen1:
            <comma (line 1 col 8) `,`>,
            (key_value_pair:
              (key:
                <string (line 1 col 10) `"b"`>
              ),
              <colon (line 1 col 13) `:`>,
              (value:
                (list:
                  <lsquare (line 1 col 15) `[`>,
                  (_gen2:
                    (value:
                      <integer (line 1 col 16) `2`>
                    ),
                    (_gen3:
                      <comma (line 1 col 17) `,`>,
                      (value:
                        <integer (line 1 col 18) `3`>
                      ),
                      (_gen3: )
                    )
                  ),
                  <rsquare (line 1 col 19) `]`>
                )
              )
            ),
            (_gen1: )
          )
        ),
        <rbrace (line 1 col 20) `}`>
      )
    )

.. code-block:: hgr

    grammar {
      lexer<python> {
        r'\s+' -> null
        r'[A-Z]+' -> :constant
        r'{' -> expression_start(:lbrace)

        mode<expression> {
          r'[0-9]+' -> :number
          r'[a-z]+' -> :identifier
          r'\+' -> :add
          r'-' -> :subtract
          r'\*' -> :multiply
          r'/' -> :divide
          r'\(' -> :lparen
          r'\)' -> :rparen
          r',' -> :comma
          r'}' -> expression_end(:rbrace)
          r'\s+' -> null
        }

        <code>
    def expression_start(context, mode, match, terminal, resource, line, col):
        return default_action(context, 'expression', match, terminal, resource, line, col)
    def expression_end(context, mode, match, terminal, resource, line, col):
        return default_action(context, 'default', match, terminal, resource, line, col)
        </code>
      }

      lexer<c> {
        "\\s+" -> null
        "[A-Z]+" -> :constant
        "{" -> expression_start(:lbrace)

        mode<expression> {
          "[0-9]+" -> :number
          "[a-z]+" -> :identifier
          "\\+" -> :add
          "-" -> :subtract
          "\\*" -> :multiply
          "/" -> :divide
          "\\(" -> :lparen
          "\\)" -> :rparen
          "," -> :comma
          "}" -> expression_end(:rbrace)
          "\\s+" -> null
        }

        <code>
    static LEXER_MATCH_T * expression_start(void * context, char * mode, char ** match_groups, TERMINAL_T * terminal, char * resource, int line, int col)
    {
        return default_action(context, "expression", match_groups, terminal, resource, line, col);
    }
    static LEXER_MATCH_T * expression_end(void * context, char * mode, char ** match_groups, TERMINAL_T * terminal, char * resource, int line, int col)
    {
        return default_action(context, "default", match_groups, terminal, resource, line, col);
    }
        </code>
      }

      lexer<java> {
        "[a-z]+" -> :identifier
        "\\{" -> expression_start(:lbrace)
        "\\s+" -> null

        mode<expression> {
          "[0-9]+" -> :number
          "\\}" -> expression_end(:rbrace)
          "\\s+" -> null
        }

        <code>
    public LexerMatch expression_start(Object context, String mode, String match, GrammarTerminalIdentifier terminal, String resource, int line, int col) {
        return default_action(context, "expression", match, terminal, resource, line, col);
    }

    public LexerMatch expression_end(Object context, String mode, String match, GrammarTerminalIdentifier terminal, String resource, int line, int col) {
        return default_action(context, "default", match, terminal, resource, line, col);
    }
        </code>
      }

      lexer<javascript> {
        "[a-z]+" -> :identifier
        "{" -> expression_start(:lbrace)
        "\\s+" -> null

        mode<expression> {
          "[0-9]+" -> :number
          "[a-z]+" -> :identifier
          "}" -> expression_end(:rbrace)
          "\\s+" -> null
        }

        <code>
    function expression_start(context, mode, match, terminal, resource, line, col) {
        return default_action(context, "expression", match, terminal, resource, line, col);
    }
    function expression_end(context, mode, match, terminal, resource, line, col) {
        return default_action(context, "default", match, terminal, resource, line, col);
    }
        </code>
      }

      parser<ll1> {
        $start = list($item)
        $item = :constant | :lbrace $e :rbrace -> $1
        $e = parser<expression> {
          (*:left) $e = $e :add $e -> Add(lhs=$0, rhs=$2)
          (-:left) $e = $e :subtract $e -> Subtract(lhs=$0, rhs=$2)
          (*:left) $e = $e :multiply $e -> Multiply(lhs=$0, rhs=$2)
          (-:left) $e = $e :divide $e -> Divide(lhs=$0, rhs=$2)
          (-:left) $e = :identifier <=> :lparen list($e, :comma) :rparen -> FunctionCall( name=$$, params=$2 )
          (*:unary) $e = :subtract $e -> UMinus(arg=$1)
          $e = :lparen $e :rparen -> $1
          $e = :identifier
          $e = :number
        }
      }
    }


parser.py

.. code-block:: python

    >>> import hermes
    >>> with open('test.gr') as fp:
    ...     json_parser = hermes.compile(fp)
    ...
    >>> tree = json_parser.parse('{"a": 1, "b": [2,3]}')
    >>> print(tree.dumps(indent=2))
    (json:
      (obj:
        <lbrace (line 1 col 1) `{`>,
        (_gen0:
          (key_value_pair:
            (key:
              <string (line 1 col 2) `"a"`>
            ),
            <colon (line 1 col 5) `:`>,
            (value:
              <integer (line 1 col 7) `1`>
            )
          ),
          (_gen1:
            <comma (line 1 col 8) `,`>,
            (key_value_pair:
              (key:
                <string (line 1 col 10) `"b"`>
              ),
              <colon (line 1 col 13) `:`>,
              (value:
                (list:
                  <lsquare (line 1 col 15) `[`>,
                  (_gen2:
                    (value:
                      <integer (line 1 col 16) `2`>
                    ),
                    (_gen3:
                      <comma (line 1 col 17) `,`>,
                      (value:
                        <integer (line 1 col 18) `3`>
                      ),
                      (_gen3: )
                    )
                  ),
                  <rsquare (line 1 col 19) `]`>
                )
              )
            ),
            (_gen1: )
          )
        ),
        <rbrace (line 1 col 20) `}`>
      )
    )
    >>> print(tree.toAst().dumps(indent=2))
    (JsonObject:
      values=[
        (KeyValue:
          key=<string (line 1 col 2) `"a"`>,
          value=<integer (line 1 col 7) `1`>
        ),
        (KeyValue:
          key=<string (line 1 col 10) `"b"`>,
          value=(JsonList:
            values=[
              <integer (line 1 col 16) `2`>,
              <integer (line 1 col 18) `3`>
            ]
          )
        )
      ]
    )
    >>>
