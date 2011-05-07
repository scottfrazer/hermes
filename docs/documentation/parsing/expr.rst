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
                                          The resulting parse tree is (<terminal>: _expr, _expr).
``_expr := <terminal> + _expr``           Unary operator notation.  Must have an entry in the ``"binding_power"``
                                          section with unary associativity.  The resulting parse tree is
                                          (<terminal>: _expr).
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

Example 2: Parsing Function Calls
---------------------------------
