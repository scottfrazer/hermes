Expression Parsing
==================

Expression parsing will look quite a bit similar but act quite a bit differently from LL(1) parsing.  The algorithm behind expression parsing in Hermes is called Pratt Parsing.  It's used to deal with the oddities that arise from trying to build infix parsing expressions with operator precedence.  

The expression parser in Hermes is considered a sub-parser.  All rules defined within the expression parser are visible to the standard LL(1) parser by a nonterminal called ``_expr``.

File Format
-----------

Expression parsing rules are defined in a new section called ``"expr"``.  Within that, you can specify ``"binding_power"`` and ``"rules"``.  Rules are much like the are in LL(1) parsing, expressing how to translate a non-terminal into one or more morphemes.  The binding power section allows you to specify the associativity of operator terminals and the binding power that we can use to disambiguate situations where we have a choice of operators to apply.

The grammar below describes a grammar that can correctly parse ``a + b * c`` as ``a + (b * c)```:

.. code-block:: python

    {
      "ll1": {
        "start": "S",
        "rules": [
            "S := _expr"
        ]
      },
      "expr": {
        "binding_power": [
          {"associativity": "left", "terminals": ["add", "subtract"]},
          {"associativity": "left", "terminals": ["multiply", "divide"]}
        ],
        "rules": [
            "_expr := _expr + 'add' + _expr",
            "_expr := _expr + 'subtract' + _expr",
            "_expr := _expr + 'multiply' + _expr",
            "_expr := _expr + 'divide' + _expr",
            "_expr := 'a' | 'b' | 'c'"
        ]
      }
    }

The binding power can have one of three associativity values: left, right, and unary.  The order of the items in the binding_power list is the order of their binding power.  The greater its index in the list, the tighter the operators bind.

Specifying Expression Rules
---------------------------

Specifying expression rules is much the same as it is for LL(1) grammar rules.  The big difference is that with expression parsing, we can now specify a certain subset of rules that would normally cause ambiguity.  Listed below are these subset of rules and how to specify them:

=======================================   =======================================================================
Rule Form                                 Notes
=======================================   =======================================================================
``_expr := _expr + <terminal> + _expr``   Infix operator notation.  Must have an entry in the ``"binding_power"`` 
                                          section with left or right associativity to resolve ambiguitities.  
                                          The resulting parse tree is (_expr: _expr, <terminal> + _expr).
``_expr := <terminal> + _expr``           Unary operator notation.  Must have an entry in the ``"binding_power"``
                                          section with unary associativity.  The resulting parse tree is
                                          (_expr: <terminal> + _expr).
=======================================   =======================================================================

Example 1: Mathematical Statements
----------------------------------

Expanding on the grammar to parse operators with precedence, let's add parenthesis support:

.. code-block:: python

    {
      "ll1": {
        "start": "S",
        "rules": [
            "S := _expr"
        ]
      },
      "expr": {
        "binding_power": [
          {"associativity": "left", "terminals": ["add", "subtract"]},
          {"associativity": "left", "terminals": ["multiply", "divide"]}
        ],
        "rules": [
            "_expr := _expr + 'add' + _expr",
            "_expr := _expr + 'subtract' + _expr",
            "_expr := _expr + 'multiply' + _expr",
            "_expr := _expr + 'divide' + _expr",
            "_expr := 'a' | 'b' | 'c'",
            "_expr := 'lparen' + _expr + 'rparen'
        ]
      }
    }

The grammar analysis shows a new special terminal, λ, which is used as a placeholder to represent an expression.

.. code-block:: python

     -- Terminals --
    'add', 'subtract', 'multiply', 'divide', 'a', 'b', 'c', 'lparen', 'rparen', ε, σ, λ

     -- Non-Terminals --
    S, _expr

     -- Normalized Grammar -- 
    S := _expr

     -- Expression Grammar -- 
    _expr := _expr 'add' _expr
    _expr := _expr 'subtract' _expr
    _expr := _expr 'multiply' _expr
    _expr := _expr 'divide' _expr
    _expr := 'a'
    _expr := 'b'
    _expr := 'c'
    _expr := 'lparen' _expr 'rparen'

     -- First sets --
    S = {'b', 'c', 'a', λ, 'lparen'}
    _expr = {'b', 'c', 'a', λ, 'lparen'}

     -- Follow sets --
    S = {σ}
    _expr = {'add', 'rparen', 'subtract', 'divide', 'multiply', σ}

    Grammar is LL(1)!

We can use this grammar to parse expressions with order of operations being applied if there are no parenthesis:

.. code-block:: bash

    $ hermes parse math.zgr --tokens=a,multiply,lparen,b,add,c,rparen
    (S: (_expr: a, multiply, (_expr: lparen, (_expr: b, add, c), rparen)))
    $ hermes parse math.zgr --tokens=a,multiply,b,add,c
    (S: (_expr: (_expr: a, multiply, b), add, c))

Example 2: Parsing Function Calls
---------------------------------

C-style function calls can be parsed with an expression parser as well.  This task is normally difficult for LL(1) Parsers because it requires two tokens of look ahead to distinguish between a function call and just a regular identifier.

.. code-block:: javascript

    {
      "ll1": {
        "start": "start",
        "rules": [
          "start := list(sub, 'comma') -> Statements( list=$0 )",
          "sub := item -> Item( name=$0 ) | _expr",
          "item := 'b' | 'a'"
        ]
      },
      "expr": {
        "binding_power": [
          {"associativity": "left", "terminals": ["add", "subtract"]},
          {"associativity": "left", "terminals": ["multiply", "divide"]},
          {"associativity": "unary", "terminals": ["subtract"]},
          {"associativity": "left", "terminals": ["lparen"]}
        ],
        "rules": [
          "_expr := 'identifier' + ^'lparen' + list(_expr, 'comma') + 'rparen' -> FuncCall( name=$0, params=$2 )",
          "_expr := _expr + 'multiply' + _expr -> Mul( l=$0, r=$2 )",
          "_expr := _expr + 'divide' + _expr -> Div( l=$0, r=$2 )",
          "_expr := _expr + 'add' + _expr -> Add( l=$0, r=$2 )",
          "_expr := _expr + 'subtract' + _expr -> Sub( l=$0, r=$2 )",
          "_expr := 'subtract' + _expr -> UMinus( arg=$1 )",
          "_expr := 'lparen' + _expr + 'rparen' -> $1",
          "_expr := 'identifier' | 'number'"
        ]
      }
    }

Notice how the first expression rule has a ``^`` character before the lparen terminal.  Everything before the lparen terminal is processed as if it were its own rule and then the result of that is passed in to the function to parse the entire rule.  If we leave out the special ``^`` character, Hermes reports one grammar conflict:

.. code-block:: bash

     -- NUD conflict -- 
    Terminal 'identifier' requires two different NUD() functions.  Cannot choose between these rules:

    (Rule-0) _expr := 'identifier' 'lparen' <EXPR LIST (_expr, 'comma')> 'rparen'
    (Rule-7) _expr := 'identifier'

The ambiguity becomes apparent in that we need to look ahead more than just one token in order to determine which rule above to use

We can now use this grammar to parse an expression like ``1+f(0)``

.. code-block:: bash

    $ hermes parse func.zgr --tokens=number,add,identifier,lparen,number,rparen
    (start: (_gen0: (sub: (_expr: number, add, (_expr: identifier, lparen, [number], rparen))), (_gen1: )))
    $ hermes parse func.zgr --tokens=number,add,identifier,lparen,number,rparen --ast
    (Statements: list=[(Add: r=(FuncCall: params=[number], name=identifier), l=number)])
