Grammar File Format
===================

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

LL(1) Parsing Format
--------------------

The LL(1) section has two properties: the starting point and the list of rules.  The "start" property specifies a nonterminal that is designated as the entry point to the parser.  The "rules" section is a list of strings that specify the generative rules.

All parsing rules, for expression parsing and LL(1) parsing have the same basic format: ``<nonterminal> := <production>``.  A production has the format: ``(<nonterminal> | <terminal> | <macro>)*``.

Non-terminals are specified as simple strings.  Terminals are distinguished from non-terminals by being enclosed in single quotes.  For example, a simple grammar that accepts either an 'x' or a 'y' terminal would be specified as follows:

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

