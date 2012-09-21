Hermes Parser Generator
=======================

Hermes is a parser generator for LL(1) grammars with extensions to parse expressions. 

[![Build Status](https://secure.travis-ci.org/scottfrazer/hermes.png)](http://travis-ci.org/scottfrazer/hermes)

Pre-requisites
--------------

* Python 3.0+
* moody
* xtermcolor

Installation
------------

If you don't have Distribute:

```bash
$ python distribute_setup.py
```

Then:

```bash
$ python setup.py install
```

Documentation
-------------

For full documentation, go to: http://hermes.readthedocs.org/

Hermes is a parser generator that takes as input a grammar file and generates a parser in one of three languages (Java, C, Python).

```
$ cat grammar.zgr
{
  "ll1": {
    "start": "start",
    "rules": [
      "Start := Sub + 'semi'",
      "Sub := 'a' + Sub + 'b' | _empty"
    ]
  }
}
```

Then, generate the C source code and compile it:

```
$ hermes generate --language=c --add-main grammar.zgr
$ gcc -o parser grammar_parser.c parser_common.c parser_main.c -g -Wall -pedantic -ansi -std=c99
```

Finally, run the parser with a set of pre-defined tokens (this would be output from the lexical analyzer):

```
$ cat tokens
[
  {"terminal": "a", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "a", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "b", "line": 0, "col": 0, "resource": "tokens", "source_string": "B"},
  {"terminal": "b", "line": 0, "col": 0, "resource": "tokens", "source_string": "b"},
  {"terminal": "semi", "line": 0, "col": 0, "resource": "tokens", "source_string": ""}
]
$ cat tokens | ./parser grammar parsetree
(start:
  (sub:
    a,
    (sub:
      a,
      (sub: ),
      b
    ),
    b
  ),
  semi
)
```

Contact
-------

Scott Frazer <scott.d.frazer (at) gmail (dot) com>
