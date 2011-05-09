AST Syntax
==========

ASTs have non-terminals, terminals, and lists (arrays) as primitives.  Terminals and nonterminals translate directly to the AST and the list macro will become a list in the abstract syntax tree.

The general syntax for an AST transformation is:

``ObjectName( attr0=$x, attr1=$y, attrn=$n )``

Where x, y, and n are integers greater than or equal to zero.  The object name and attribute names are arbitrary strings that add semantics.  The elements following the dollar sign ($x, $y, $n, etc) represent elements in the parse tree.  We can connect the parse tree to an AST by specifying the rule as follows:

``s := x + y + 'z' -> MyObject( first=$0, third=$2 )``

Here we are specifying that 'first' will be the non-terminal ``x`` and 'third' will be the terminal ``z``.

AST specifications are not required to create objects.  Sometimes you want part of a syntax tree.  For these cases, we can use what's called an AST translation.  A common use of this is to remove separator characters or if the rule in question is more of an intermediary rule.  For example, if we want to support parenthesized expressions, we might want to specify the parse tree and AST translation as follows:

``_expr := 'lparen' + _expr + 'rparen' -> $1``

Here we are just returning the AST for the inner ``_expr`` non-terminal.  This rule itself doesn't need to create its own object, it just needs to return the object for the inner expression.

If no AST translation or specification is in the grammar rule explicitly, then an implicit AST translation of $0 will be used.