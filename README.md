# Hermes Parser Generator

[![Build Status](https://travis-ci.org/scottfrazer/hermes.svg?branch=develop)](https://travis-ci.org/scottfrazer/hermes)

Hermes is a parser generator for LL(1) grammars with extensions to parse expressions.

Hermes can target 5 languages:

* Python
* Go
* Java
* C
* JavaScript

# Documentation

Full documentation is located [here](DOCS.md).

# Quick Start

```
>>> import hermes
>>> with open('test.gr') as fp:
...     json_parser = hermes.compile(fp)
...
>>> tree = json_parser.parse('{"a": 1, "b": [2,3]}')
>>> print(tree.dumps(indent=2))
(json:
  (obj:
    <lbrace (line 1 col 1) `{`>,
    (_gen0:
      (key_value_pair:
        (key:
          <string (line 1 col 2) `"a"`>
        ),
        <colon (line 1 col 5) `:`>,
        (value:
          <integer (line 1 col 7) `1`>
        )
      ),
      (_gen1:
        <comma (line 1 col 8) `,`>,
        (key_value_pair:
          (key:
            <string (line 1 col 10) `"b"`>
          ),
          <colon (line 1 col 13) `:`>,
          (value:
            (list:
              <lsquare (line 1 col 15) `[`>,
              (_gen2:
                (value:
                  <integer (line 1 col 16) `2`>
                ),
                (_gen3:
                  <comma (line 1 col 17) `,`>,
                  (value:
                    <integer (line 1 col 18) `3`>
                  ),
                  (_gen3: )
                )
              ),
              <rsquare (line 1 col 19) `]`>
            )
          )
        ),
        (_gen1: )
      )
    ),
    <rbrace (line 1 col 20) `}`>
  )
)
>>> print(tree.toAst().dumps(indent=2))
(JsonObject:
  values=[
    (KeyValue:
      key=<string (line 1 col 2) `"a"`>,
      value=<integer (line 1 col 7) `1`>
    ),
    (KeyValue:
      key=<string (line 1 col 10) `"b"`>,
      value=(JsonList:
        values=[
          <integer (line 1 col 16) `2`>,
          <integer (line 1 col 18) `3`>
        ]
      )
    )
  ]
)
>>>
```

# Dependencies

* Python 3.4+
* moody-templates 0.9
* xtermcolor 1.2

# Installation

```bash
$ python setup.py install
```

Or, through pip:

```bash
$ pip install hermes-parser
```
