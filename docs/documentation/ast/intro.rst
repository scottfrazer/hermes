Introduction to ASTs
====================

an Abstract Syntax Tree (AST) is a way to add further semantics onto a parse tree and at the same time reduce it to smallest semantic representation.

What does this mean in more concrete terms?  Let's say we have a grammar rule that defines a simple C-style for statement:

``for := 'for' + 'lparen' + _expr + 'semi' + _expr + 'semi' + _expr + 'rparen' + statement``

A parse tree for one of these if statements is littered with delimiter nodes and parenthesis.  Also, we don't really know the difference between the three _expr.  What is the function of each of them?

We can imagine transforming the parse tree resulting from this rule into a data structure like this which keeps only what we need while adding necessary semantics.

``ForStmt( init=$2, cond=$4, incr=$6, body=$8 )``

This is how abstract syntax trees are defined in Hermes.

Primitives
----------

Unlike parse trees who's primitives are only non-terminals and terminals, ASTs also allow ordered lists (arrays).  In fact, a list macro in the grammar rule translates to a list primitive in the AST
