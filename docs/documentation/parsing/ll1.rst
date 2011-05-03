LL(1) Parsing
=============

File Format
-----------

The Grammar file format that hermes uses is a simple JSON document containing two main sections: one section for top-down, LL(1) grammar rules, and another for expression parsing rules.  The entry point for the parser must always be a nonterminal in the LL(1) grammar rules.

Below is a template for grammar files.  The two sections are "ll1" (that's LL1 in lowercase) and "expr".  If you do not have any expression parsing rules, this section can be left out.

.. code-block:: javascript

    {
      "ll1": {
        "start": "",
        "rules": []
      },
      "expr": {
        "binding_power": []
        "rules": []
      }
    }

The LL(1) section has two properties: the starting point and the list of rules.  The "start" property specifies a nonterminal that is designated as the entry point to the parser.  The "rules" section is a list of strings that specify the generative rules.

Specifying Grammar Rules
------------------------

A grammar rule describes how to transform a nonterminal into a series of one or more morphemes.  A morpheme is either a nonterminal or terminal (or list macro but we'll get to that later!).  In Hermes, morphemes are symbolic names which describes their content but may not represent the literal tokenized string that was matched by the lexer.

For example, one might write a rule for generating a C-style for statement as ``for_stmt := 'for' + 'lparen' + expr + 'semi' + expr + 'semi' + expr + 'rparen'``.  Notice that we are using 'lparen' to signify a left paren, and a 'semi' to signify a semicolon.

*Grammar Rule Format*
    rule: ``<nonterminal> := <production>``

    production: ``<morpheme>+``

    morpheme: ``<terminal> | <nonterminal> | <macro>``

    terminal: ``<simple_terminal> | <abstract_terminal>``

    abstract_terminal: ``<empty_string>``

Non-terminals are represented in the grammar as strings of letters, numbers, and underscores.  Terminals are represented the same way, except they're enclosed in single quotes.  Finally, the empty string can be represented as a lowercase epsilon (ε) or the ASCII equivelant, _empty.

*Morpheme Format*
    nonterminal: ``[a-zA-Z_]+``

    terminal: ``'[a-zA-Z_]+'``

    empty_string: ``(ε | _empty)``


Example 1: 'Hello World' Grammar
--------------------------------

This simple grammar illustrates the one of the simplest non-trivial grammars.  It simply accepts exactly one 'x' or 'y' terminal.

.. code-block:: javascript

    {
      "ll1": {
        "start": "S",
        "rules": [
            "S := 'x' | 'y'"
        ]
      }
    }

In this grammar, the start symbol is S and there is one rule describing how the nonterminal S can be reduced to either an 'x' or 'y' nonterminal.  It's important to note that the '|' symbol can be used to specify multiple rules from within the same line.  It's simply a convenient shorthand.  The above grammar is equivalent to the following grammar:

.. code-block:: javascript

    {
      "ll1": {
        "start": "S",
        "rules": [
            "S := 'x'",
            "S := 'y'"
        ]
      }
    }

The grammar analysis is fairly straightforward.  There's a new abstract terminal that's listed in the analysis which is the σ (lowercase sigma).  This terminal represents the end of the token stream.  Notice how in the follow set for the terminal S is σ, signifying that the token stream can end after S is processed.

.. code-block:: bash

    $ hermes analyze simple.zgr 
     -- Terminals --
    'y', 'x', 'σ', 'ε'

     -- Non-Terminals --
    s

     -- Normalized Grammar -- 
    S := 'x'
    S := 'y'

     -- First sets --
    S = {'x', 'y'}

     -- Follow sets --
    S = {σ}

    Grammar is LL(1)!

We can try this out with a few sample inputs to validate that it's working as we expect:

.. code-block:: bash

    $ hermes parse simple.zgr --tokens=x
    (s: x)
    $ hermes parse simple.zgr --tokens=y
    (s: y)
    $ hermes parse simple.zgr --tokens=z
    Parser instance has no attribute 'TERMINAL_Z'
    $ hermes parse simple.zgr --tokenx=x,y
    Syntax Error: Finished parsing without consuming all tokens.

Example 2: Complete Grammar
---------------------------

Here's a simple grammar that accepts an ``'a'``, ``'b'``, or a parenthesized expression (``ParenExpr``).  This grammar illustrates every element of an LL(1) parser rule.

.. code-block:: javascript

    {
      "ll1": {
        "start": "program",
        "rules": [
          "Program := 'a' | 'b' | ParenExpr | ε",
          "ParenExpr := 'lparen' + Program + 'rparen' | ε"
        ]
      }
    }

The analysis:

.. code-block:: bash

   $ hermes analyze complete.zgr 
     -- Terminals --
    'a', 'σ', 'b', 'rparen', 'ε', 'lparen'

     -- Non-Terminals --
    parenexpr, program

     -- Normalized Grammar -- 
    Program := 'a'
    Program := 'b'
    Program := ParenExpr
    Program := ε
    ParenExpr := 'lparen' Program 'rparen'
    ParenExpr := ε

     -- First sets --
    ParenExpr = {'lparen', ε}
    Program = {'lparen', 'b', ε, 'a'}

     -- Follow sets --
    ParenExpr = {σ, 'rparen'}
    Program = {σ, 'rparen'}

    Grammar is LL(1)!

Sample runs:

.. code-block:: bash

    $ hermes parse complete.zgr --tokens=a
    (program: a)
    $ hermes parse complete.zgr --tokens=b
    (program: b)
    $ hermes parse complete.zgr --tokens=lparen,lparen,b,rparen,rparen
    (program: (parenexpr: lparen, (program: (parenexpr: lparen, (program: b), rparen)), rparen))

