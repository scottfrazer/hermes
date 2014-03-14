# Hermes Parser Generator

Hermes is a parser generator for LL(1) grammars with extensions to parse expressions. 

[![Build Status](https://secure.travis-ci.org/scottfrazer/hermes.png)](http://travis-ci.org/scottfrazer/hermes)
[![Coverage Status](https://coveralls.io/repos/scottfrazer/hermes/badge.png)](https://coveralls.io/r/scottfrazer/hermes)
[![Latest Version](https://pypip.in/v/hermes-parser/badge.png)](https://pypi.python.org/pypi/hermes-parser/)
[![License](https://pypip.in/license/hermes-parser/badge.png)](https://pypi.python.org/pypi/hermes-parser/)

# Dependencies

* Python 3.3+
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

# Documentation

For full documentation, go to: http://hermes.readthedocs.org/

## Introduction

Hermes is a parser generator that takes as input a grammar file and generates a parser in one of three languages (Java, C, Python).  The generated parser will take as input a list of tokens.  The tokenization process must be done outside of Hermes.

The following grammar will accept input, and return a parse tree, if the input tokens contains any number of `a` tokens followed by the same number of `b` tokens:

```
grammar {
  parser<ll1> {
    $start = $sub + :semi
    $sub := :a + $sub + :b | :_empty
  }
}
```

## Grammar File Specification

Grammar files are specified as a JSON object that typically has the `.gr` extension.  A skeleton grammar file looks like this:

```
grammar {
  parser<ll1> {
    ... rules ...
    $e = parser<expressoin> {
      ... expression rules ...
    }
  }
}
```

There are two main sections here: LL(1) and Expression grammars.  LL(1) grammars are the simplest, requiring only a set of rules and a starting nonterminal.  Expression parsers are similar, except they require a bit more information, like which nonterminal to represent the expression as.

The syntax for expressing grammar rules is:

```
$Nonterminal := [$Nonterminal | :Terminal]+
```

Nonterminals must conform to the regular expression: `\$[a-zA-Z0-9_]+` (i.e. variable names preceded by a $)
Terminals must conform to the regular expression: `:[a-zA-Z0-9_]+` (i.e. variable names preceded by a :)

Some examples of grammar rules:

```
$properties = :lbrace $items :rbrace
$items = :item $items_sub
$items_sub = :comma :item $items_sub
$items_sub = :_empty
```

Grammar rules can be combined for brevity:

```
$N := :a
$N := :b
```

Is the same as:

```
$N := :a | :b
```

## Generating a Parser

Using the grammar from the introduction, we can generate a parser in the C programming language with the following command:

```bash
$ hermes generate --language=c --add-main grammar.zgr
```

The output of this command will be a bunch of .c and .h files in the current directory.  Compile the code as follows:

```bash
$ cc -o parser *.c -std=c99
```

## Running the Parser

As input, the parser needs a list of tokens.  Programmatically, the tokens can be specified as objects, but for running the main() method that Hermes generates, the tokens file format is defined to look like this:

```json
[
  {"terminal": "a", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "a", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "b", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "b", "line": 0, "col": 0, "resource": "tokens", "source_string": ""},
  {"terminal": "semi", "line": 0, "col": 0, "resource": "tokens", "source_string": ""}
]
```

This input specifies the following token stream: `a`, `a`, `b`, `b`, `semi`.

With the tokens file created (or generated), we can run our newly compiled parser and print out a parsetree (or syntax error):

```
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
