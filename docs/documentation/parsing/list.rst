The List Macro
==============

Some tasks are quite common when writing grammar rules.  One of these tasks is generating lists of nonterminals.  A program is a list of statements, a hashmap is a list of key/value pairs, etc.  Hermes introduces the concept of grammar macros that expand to normal grammar rules for this common task.

The syntax of the list macro is ``list(<nonterminal>, <terminal>?)`` Where the first parameter describes the nonterminal that in which zero or more will be matched.  the optional second parameter is the separator between the nonterminals.  For example, creating a list of expressions separated by commas?

Macro Expansion
---------------

Describe how the list macro expands

Example 1: Simple List
----------------------

.. code-block:: javascript

    {
      "ll1": {
        "start": "s",
        "rules": [
          "S := list(T)",
          "T := 'x' | 'y'"
        ]
      }
    }

.. code-block:: bash

    $ hermes analyze simple_list.zgr
     -- Terminals --
    'y', 'x', 'σ', 'ε'

     -- Non-Terminals --
    s, t, tmp0

     -- Normalized Grammar -- 
    tmp0 := T tmp0
    tmp0 := ε
    S := tmp0
    T := 'x'
    T := 'y'

     -- First sets --
    T = {'x', 'y'}
    tmp0 = {'x', ε, 'y'}
    S = {'x', 'y'}

     -- Follow sets --
    tmp0 = {σ}
    S = {σ}
    T = {'x', 'y', σ}

    Grammar is LL(1)!

.. code-block:: bash

    $ hermes parse ~/j.zgr --tokens=x,y,x,y
    (s: (tmp0: (t: x), (tmp0: (t: y), (tmp0: (t: x), (tmp0: (t: y), (tmp0: ))))))
    $ hermes parse simple_list.zgr --tokens=x,y,x,y,x,x,x
    (s: (tmp0: (t: x), (tmp0: (t: y), (tmp0: (t: x), (tmp0: (t: y), (tmp0: (t: x), (tmp0: (t: x), (tmp0: (t: x), (tmp0: )))))))))
    $ hermes parse ~/j.zgr --tokens=x
    (s: (tmp0: (t: x), (tmp0: )))
