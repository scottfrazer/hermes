Introduction to ASTs
====================

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