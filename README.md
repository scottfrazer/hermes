# Hermes Parser Generator

Hermes is a parser generator for LL(1) grammars with extensions to parse expressions. 

[![Build Status](https://secure.travis-ci.org/scottfrazer/hermes.png)](http://travis-ci.org/scottfrazer/hermes)
[![Coverage Status](https://coveralls.io/repos/scottfrazer/hermes/badge.png)](https://coveralls.io/r/scottfrazer/hermes)
[![Latest Version](https://pypip.in/v/hermes-parser/badge.png)](https://pypi.python.org/pypi/hermes-parser/)
[![License](https://pypip.in/license/hermes-parser/badge.png)](https://pypi.python.org/pypi/hermes-parser/)

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

# Documentation

For full documentation, go to: http://hermes.readthedocs.org/

## Introduction

Hermes is a parser generator that takes as input a grammar file and generates a parser in one of four target languages (Python, C, Java, JavaScript).  The generated code can be used as part of a separate code base or stand-alone via a front-end interface.

The following grammar will accept input, and return a parse tree, if the input tokens contains any number of `:a` tokens followed by the same number of `:b` tokens, followed by a terminating semicolon (`:semi`):

```
grammar {
  lexer<python> {
    r'a' -> :a
    r'b' -> :b
    r';' -> :semi
  }
  parser<ll1> {
    $start = $sub + :semi
    $sub := :a + $sub + :b | :_empty
  }
}
```

## Grammar File Specification

Grammar files are specified in Hermes Grammar Format that typically has the `.gr` extension.  A skeleton grammar file looks like this:

```
grammar {
  lexer<c> {
    ... lexer regular expressions ...
  }
  parser<ll1> {
    ... rules ...
    $e = parser<expression> {
      ... expression rules ...
    }
  }
}
```

Breaking down the grammar definition a little bit

### Lexer definition

```
lexer<c> {
  "[a-z]+" -> :word
  "[0-9]+" -> :number
}
```

This defines that a lexer will be generated in the target language specified.  Inside the braces will be rules in the form of `regex -> terminal`.  In the example above, if the *beginning* of the input string matches "[a-z]+", then a `:word` terminal will be emitted from the lexical analyzer.  If the beginning of the input stream does not match "[a-z]+", then the next expression is tried.

The lexer is optional.  If one is not provided, then an external lexer needs to be provided that outputs the right data structures that the parser can understand.

Regular expressions for the lexer are language dependent.  Here are the supported languages and the way they interpret the regular expressions:

* Python: [regex](https://docs.python.org/3.4/library/re.html) module in standard library
* C: [libpcre2](http://www.pcre.org/)
* Java: [java.util.regex](http://docs.oracle.com/javase/7/docs/api/java/util/regex/package-summary.html).  Specifically, the parameter to [Pattern.compile()](http://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html#compile(java.lang.String))
* JavaScript: [RegExp()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp) class

### LL(1) Parser Rules

LL(1) rules define how terminals (from the lexer) group together to form nonterminals.

The syntax for expressing grammar rules is:

```
$Nonterminal := [$Nonterminal | :Terminal]+
```

Nonterminals must conform to the regular expression: `\$[a-zA-Z0-9_]+` (i.e. variable names preceded by a `$`)
Terminals must conform to the regular expression: `:[a-zA-Z0-9_]+` (i.e. variable names preceded by a `:`)

Some examples of grammar rules:

```
$properties = :lbrace $items :rbrace
$items = :item $items_sub
$items_sub = :comma :item $items_sub
$items_sub = :_empty
```

Grammar rules can be combined for brevity:

```
$N = :a
$N = :b
```

Is the same as:

```
$N = :a | :b
```

The special terminal, `:_empty` refers to the empty string.  The rule `$N = :a :_empty :b` is the same as `$N = :a :b`.

### Expression Sub-Parsers

...

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
