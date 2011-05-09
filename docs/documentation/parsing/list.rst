The List Macro
==============

Some tasks are quite common when writing grammar rules.  One of these tasks is generating lists of nonterminals.  A program is a list of statements, a hashmap is a list of key/value pairs, etc.  Hermes introduces the concept of grammar macros that expand to normal grammar rules for this common task.

The syntax of the list macro is ``list(<nonterminal>, <terminal>?)`` Where the first parameter describes the nonterminal that in which zero or more will be matched.  the optional second parameter is the separator between the nonterminals.  For example, creating a list of expressions separated by commas?

Macro Expansion
---------------

The list macro is expanded into grammar rules.  ``list(<nonterminal>)`` is replaced by a new nonterminal ``_gen[0-9]+``.  For example, if we have a grammar with two rules: ``S := list(N)`` and ``N := 't'``, this would be expanded to:

.. code-block:: pascal

    S := _gen0
    _gen0 := N + _gen0 | ε
    N := 't'

Whereas, if we have the same rule but with a terminal as the separator: ``S := list(N, 'x')`` and ``N := 't'``, this would be expanded to:

.. code-block:: pascal

    S := _gen0
    _gen0 := N + _gen1 | ε
    _gen1 := 'x' + N + _gen1 | ε

It's important to note that the macro is not entirely identical to the rules it generates.  In terms of straight LL(1) Parsing, they're equivalent.  However, this macro translates to a list primitive for the abstract syntax tree.  More information on that in the section on abstract syntax trees.

Example 1: Simple List
----------------------

This is an example of a simple list of the nonterminal T which can be an 'x' or 'y' terminal.

.. code-block:: javascript

    {
      "ll1": {
        "start": "s",
        "rules": [
          "S := list(T) -> MyList( items=$0 )",
          "T := 'x' | 'y'"
        ]
      }
    }

The analysis reveals the expansion of the list macro in the normalized grammar:

.. code-block:: bash

    $ hermes analyze simple_list.zgr
     -- Terminals --
    'y', 'x', 'σ', 'ε'

     -- Non-Terminals --
    s, t, _gen0

     -- Normalized Grammar -- 
    _gen0 := T _gen0
    _gen0 := ε
    S := _gen0
    T := 'x'
    T := 'y'

     -- First sets --
    T = {'x', 'y'}
    _gen0 = {'x', ε, 'y'}
    S = {'x', 'y'}

     -- Follow sets --
    _gen0 = {σ}
    S = {σ}
    T = {'x', 'y', σ}

    Grammar is LL(1)!

Finally, we can see the parse trees that result from a series of x and y terminals:

.. code-block:: bash

    $ hermes parse simple_list.zgr --tokens=x,y,x,y
    (s: (_gen0: (T: x), (_gen0: (T: y), (_gen0: (T: x), (_gen0: (T: y), (_gen0: ))))))
    $ hermes parse simple_list.zgr --tokens=x,y,x,y,x,x,x
    (s: (_gen0: (T: x), (_gen0: (T: y), (_gen0: (T: x), (_gen0: (T: y), (_gen0: (T: x), (_gen0: (T: x), (_gen0: (T: x), (_gen0: )))))))))
    $ hermes parse simple_list.zgr --tokens=x
    (s: (_gen0: (T: x), (_gen0: )))

We also defined an abstract syntax tree (AST) transformation for this parse tree.  If we attach the --ast flag, we can get the string representation of the resulting abstract syntax tree.  Notice how the list macro translated to a list primitive in the AST.

.. code-block:: bash

    $ hermes parse simple_list.zgr --tokens=x,y,x,x,y,y --ast
    (MyList: items=[x, y, x, x, y, y])

