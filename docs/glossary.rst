.. _glossary:

========
Glossary
========

.. glossary::

    Terminal
        A symbol that itself is irreducible to a simpler form.  A terminal is usually a syntactic element of the source code that's being parsed.  There can be no rule that converts a terminal to another element.

        Consider the C statement ``if(a) b;``.  A lexer would break this string into the following terminals: 'if', '(', 'identifier', ')', 'identifier', ';'

        Often times, and throughout this documentation, the term 'token' and 'terminal' are interchangeable.

    Special Terminal
        A special terminal is one that represents something else.  These are denoted with greek letters.  There are three special terminals:

        ε (U+03B5) - Refers to the empty string.  If there's a rule ``<nonterminal> := &epsilon;``, the nonterminal could reduce to nothing

        λ (U+03BB) - Represents an expression (via the built-in expression parser)

        σ (U+03C3) - Represents the end of the token stream.

    Non-Terminal
        A nonterminal symbol is one that is a composite of one or more terminals and/or nonterminals.

    Rule
        A grammar rule, sometimes called a production rule, explains how to transform a nonterminal into a series of terminals and/or nonterminals.  In Hermes, a grammar rule is structured as follows:

        ``<nonterminal> := (<nonterminal> | <terminal>)*``

        Where * represents the `Kleene Star <http://en.wikipedia.org/wiki/Kleene_star>`_

    Compound Rule
        Like a rule, but might contain more than one rule or an AST translation.  For example:

        ``<nonterminal-1> := <nonterminal-2> + <terminal-1> -> Node(var = $0) | <nonterminal-3>``

        A compound rule is what you can define in a Hermes grammar file.  The exact syntax of a compound rule is defined in section on the Hermes grammar file format.

    Parse Tree

        Sometimes called a concrete syntax tree (CST), a parse tree is an ordered tree that represents the syntactic structure of a series of terminals based on the grammar specification.  If the array of terminals cannot create a valid tree based on the grammar specification, this is recognized as a syntax error.

        The leaf nodes of the parse tree are the terminals and the interior nodes are non-terminals.

    Abstract Syntax Tree (AST)

        An abstract syntax tree is a way of converting a parse tree into a more usable, semantic format.  Raw parse trees are often messy and have many levels of nested children making it hard to make good use of a parse tree.

        A parse tree only has two primitives: terminals and nonterminals.  An abstract syntax tree has terminals, nonterminals, and lists (arrays) as primitive types.  On top of that, ASTs add a further level of semantics to the parse tree suitable for interpretation or further compilation.
