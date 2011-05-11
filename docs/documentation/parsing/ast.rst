Abstract Syntax Trees
=====================

Introduction
------------

an Abstract Syntax Tree (AST) is a way to add further semantics onto a parse tree and at the same time reduce it to smallest semantic representation.  For example, Let's say we have a grammar rule that defines a simple C-style for statement:

``for := 'for' + 'lparen' + _expr + 'semi' + _expr + 'semi' + _expr + 'rparen' + statement``

A parse tree for one of these if statements is littered with delimiter nodes and parenthesis.  Also, we don't really know the difference between the three _expr.  What does each one mean?

To solve this problem, we can imagine transforming the parse tree resulting from this rule into a data structure like this which keeps only what we need while adding necessary semantics to each _expr non-terminal.

``ForStmt( init=$2, cond=$4, incr=$6, body=$8 )``

ASTs are simply a way of transforming a parse tree into a form that's suitable for further processing and to provide intuitive and meaning semantics.

Why Use ASTs?
-------------

You may have noticed that ASTs only really add semantics.  You don't necessarily need to translate to an AST in order to do meaningful work.  A parse tree itself contains all data necessary to process/compile the code in question.  However, ASTs provide a useful intermediate representation.  It's easy to see with the for-statement example that a control flow graph can easily be deduced from the AST.  Also, constructs like lists look exceedingly ugly in parse trees.  They consist of 2 or more rules with a whole bunch of generated nonterminals.  Converting to an AST will make all list macros into arrays which makes it easy to iterate over and process.

Moreover, it's easier to write an ``exec()`` function for each AST node than it is for a parse tree node.  This comes in handy especially if your interested in making a language that executes directly from AST and doesn't compile further into bytecode or machine code.

It's recommended that for any non-trivial grammar, that AST definitions are given for each rule.  Trust me, it will save lots of headaches in the future.

Syntax
------

ASTs have non-terminals, terminals, and lists (arrays) as primitives.  Terminals and nonterminals translate directly to the AST and the list macro will become a list in the abstract syntax tree.

The general syntax for an AST transformation is:

.. code-block:: pascal

    ObjectName( attr0=$x, attr1=$y, attrn=$n )

Where x, y, and n are integers greater than or equal to zero.  The object name and attribute names are arbitrary strings that add semantics.  The elements following the dollar sign ($x, $y, $n, etc) represent elements in the parse tree.  We can connect the parse tree to an AST by specifying the rule as follows:

.. code-block:: pascal

    s := x + y + 'z' -> MyObject( first=$0, third=$2 )

Here we are specifying that 'first' will be the non-terminal ``x`` and 'third' will be the terminal ``z``.

AST specifications are not required to create objects.  Sometimes you want part of a syntax tree.  For these cases, we can use what's called an AST translation.  A common use of this is to remove separator characters or if the rule in question is more of an intermediary rule.  For example, if we want to support parenthesized expressions, we might want to specify the parse tree and AST translation as follows:

.. code-block:: pascal

    _expr := 'lparen' + _expr + 'rparen' -> $1``

Here we are just returning the AST for the inner ``_expr`` non-terminal.  This rule itself doesn't need to create its own object, it just needs to return the object for the inner expression.

If no AST translation or specification is in the grammar rule explicitly, then an implicit AST translation of $0 will be used.

Example 1: For Statement
------------------------

A C-like for statement has three parts: the initialization, the condition, and the iteration.  Each of these can be an expression.  The body of the for statement consists of a list of statements.  For simplicity, a statement will just be an expression or the terminal 'statement'.

Note: line breaks added for readability.

.. code-block:: javascript

    {
      "ll1": {
        "start": "forstmt",
        "rules": [
          "forstmt := 'for' + 'lparen' + _expr + 'semi' + _expr
                   + 'semi' + _expr + 'rparen' + forbody
                   -> For( init=$2, cond=$4, iter=$6, body=$8)",
          "forbody := term_stmt | 'lbrace' + stmts + 'rbrace' -> $1",
          "term_stmt := stmt + 'semi'",
          "stmt := _expr | 'statement'",
          "stmts := tlist(stmt, 'semi') | ε -> $0"
        ]
      },
      "expr": {
        "binding_power": [
            {"associativity": "left", "terminals": ["comma"]},
            {"associativity": "right", "terminals": ["eq"]},
            {"associativity": "left", "terminals": ["lt", "gt"]},
            {"associativity": "left", "terminals": ["add", "sub"]},
            {"associativity": "left", "terminals": ["mul", "div"]},
            {"associativity": "unary", "terminals": ["sub"]}
        ],
        "rules": [
          "_expr := _expr + 'add' + _expr -> Add( left=$0, right=$2)",
          "_expr := _expr + 'sub' + _expr -> Sub( left=$0, right=$2)",
          "_expr := _expr + 'lt' + _expr -> LessThan( left=$0, right=$2)",
          "_expr := _expr + 'gt' + _expr -> GreaterThan( left=$0, right=$2)",
          "_expr := _expr + 'mul' + _expr -> Mul( left=$0, right=$2)",
          "_expr := _expr + 'div' + _expr -> Div( left=$0, right=$2)",
          "_expr := _expr + 'eq' + _expr -> Assign( var=$0, value=$2)",
          "_expr := _expr + 'comma' + _expr -> Comma( left=$0, right=$2)",
          "_expr := 'identifier' | 'num'"
        ]
      }
    }

You may notice that the expression grammar seems a bit odd.  The rule ``_expr := _expr + 'eq' + _expr`` isn't actually correct.  For example, it doesn't make sense to say ``1+2=3+4``.  However, sometimes it makes sense to parse things one way and interpret them another way.  We know that the equals in C-like operator precedence has right associativity.  This is why we can write ``a = b = c = 2``, because it will process ``c = 2`` first, not ``a = b``.  The equals sign in every way *behaves* like a infix operator, but we get conflicts if we try to correct this rule.  It can be done, but the effort isn't worth it.

So how do we solve this problem?  Well it's easy to implement a function in the type checking phase that checks that all AST nodes of type 'Assign' has a 'var' attribute that's an 'identifier' terminal.  This leaves our grammar file clean and easy to understand while putting higher level type checking restrictions in a layer that uses the AST as input and returns an AST that adheres to the languages type requirements.

We can now use our parser to parse a simple C-like for loop.  Let's use this example code:

.. code-block:: c

    for( i = 0, r = 1; i < power; i = i + 1 )
        r = r * 2;

Our tokenizer would break this down into the following terminals: for, lparen, identifier, eq, num, comma, identifier, eq, num, semi, identifier, lt, num, semi, identifier, eq, identifier, add, num, rparen, identifier, eq, identifier, mul, num, semi.

Using the parse command, we see that the resulting AST comes out to:

.. code-block:: javascript

    (For:
      body=(Assign:
              var=identifier,
              value=(Mul: right=num, left=identifier)
           ),
      init=(Comma:
              right=(Assign: var=identifier, value=num),
              left=(Assign: var=identifier, value=num)
           ),
      cond=(LessThan:
              right=num,
              left=identifier
           ),
      iter=(Assign:
              var=identifier,
              value=(Add: right=num, left=identifier)
           )
    )
