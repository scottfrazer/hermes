Introduction
============

Hermes is a parser generator.  Hermes shares a lot of similarities with other parser generators like Yacc, Bison, and ANTLR.  Hermes will generate recursive descent LL(1) parsers and has support for built-in expression parsing.

Hermes can be used as a Python module or as a standalone CLI tool for analyzing grammars or parsing with your own lexer function.

Hermes handles a lot of common cases with parsing that many programmers run into.  On top of BNF-style LL(1) grammars, Hermes extends this by adding a list macro for the case when you want a list of nonterminals with a separator or not.

Expression support has always been a tough point with top-down parsers and Hermes offers an expression parser built-in.  No longer will common infix expressions be a big headache.

Finally, Hermes not only parses, it will also transform the parse tree into a more usable Abstract Syntax Tree which allows the resulting parse tree to be directly interpreted or further compiled down to bytecode much easier.
