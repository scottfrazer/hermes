Basic Usage
===========

Hermes takes as input a grammar file and as output can either generate a grammar analysis which reports if the grammar has any errors, or it can generate source code in Python to parse the grammar specified.

The grammar file is a JSON file that is structured like this:

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

This grammar example contains no grammar rules.  If we wanted to make a simple grammar that matches *n* a's followed by *n* b's and then a semicolon, the grammar would look like this:

.. code-block:: javascript

    {
      "ll1": {
        "start": "Start",
        "rules": [
          "Start := Sub + 'semi'",
          "Sub := 'a' + Sub + 'b' | ε"
        ]
      }
    }

The grammar above specifies two rules.  Each token inside of single quotes is considered a terminal, or a symbolic name of a token that's received from the lexer.  The tokens that are not in single quotes are nonterminals.  A user of the generated parser will never need to know about the nonterminals.  Notice that since we do not have any "expr" section like the first example.  Since there are no expression rules, it is not necessary to specify this.

Usually the first step is to analyze the grammar and see if there are any conflicts that are going to make it ambiguous to parse the input.  To analyze your grammar, save it as ab.zgr and use the 'analyze' sub-command:

.. code-block:: bash

    $ hermes analyze ab.zgr
     -- Terminals --
    'a', 'σ', 'b', 'ε', 'semi'

     -- Non-Terminals --
    start, sub

     -- Normalized Grammar -- 
    Start := Sub 'semi'
    Sub := 'a' Sub 'b'
    Sub := ε

     -- First sets --
    Start = {'a', 'semi'}
    Sub = {'a', ε}

     -- Follow sets --
    Start = {σ}
    Sub = {'semi', 'b'}

    Grammar is LL(1)!

Since the grammar is valid, we can now generate the parser with initial tokens (mostly used for testing) and run it so we can get a parse tree printed to stdout:

.. code-block:: bash

    $ hermes generate grammars/ab.zgr --tokens=a,a,b,b,semi
    $ python Parser.py
    (start: (sub: a, (sub: a, (sub: ), b), b), semi)

If there's a syntax error, the parser will report it:

.. code-block:: bash

    $ hermes generate grammars/ab.zgr --tokens=a,a,b,semi
    $ python Parser.py
    Unexpected symbol.  Expected b, got semi.

Using Hermes from the command line like this is useful for debugging grammars and making sure they behave the way you want but once the grammar is working, you most likely want to use it from within Python as a module to get parse tree objects and process them.  To do this, import the generated parser as a Python module.  To parse programmatically, the generated parser needs an iterable that contains objects with two methods: getId() and toAst().  The parser comes with a Terminal object that implements this interface, for convenience.

.. code-block:: python

    >>> import Parser
    >>> p = Parser.Parser()
    >>> terminals = [ \
        Parser.Terminal(p.TERMINAL_A), \
        Parser.Terminal(p.TERMINAL_B), \
        Parser.Terminal(p.TERMINAL_SEMI) ]
    >>> parsetree = p.parse(terminals, 'start')
    >>> parsetree
    <Parser.ParseTree instance at 0x100492b48>
    >>> str(parsetree)
    '(start: (sub: a, (sub: ), b), semi)'

