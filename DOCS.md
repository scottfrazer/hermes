# Hermes Parser Generator

<!---toc start-->

* [Hermes Parser Generator](#hermes-parser-generator)
* [Introduction](#introduction)
* [Quick Start](#quick-start)
* [Installation](#installation)
* [Hermes Grammar File Format](#hermes-grammar-file-format)
* [Lexical Analyzer](#lexical-analyzer)
  * [Example](#example)
  * [Lexer Algorithm](#lexer-algorithm)
  * [Specifying Lexer Rules](#specifying-lexer-rules)
  * [Cross-Language Regexes](#cross-language-regexes)
  * [Regex Enumerations & Regex Flags](#regex-enumerations--regex-flags)
  * [Lexer Stack](#lexer-stack)
  * [Regex Partials](#regex-partials)
  * [Custom Functions](#custom-functions)
    * [Python](#python)
      * [init() function](#init-function)
      * [destroy() function](#destroy-function)
      * [Token Match Function](#token-match-function)
      * [LexerContext object](#lexercontext-object)
    * [Java](#java)
      * [init() function](#init-function)
      * [destroy() function](#destroy-function)
      * [Token Match Function](#token-match-function)
      * [LexerContext Object](#lexercontext-object)
    * [C](#c)
      * [init() function](#init-function)
      * [destroy() function](#destroy-function)
      * [Token Match Function](#token-match-function)
      * [LEXER_CONTEXT_T Object](#lexer_context_t-object)
    * [JavaScript](#javascript)
      * [init() function](#init-function)
      * [destroy() function](#destroy-function)
      * [Token Match Function](#token-match-function)
      * [ctx Object](#ctx-object)
* [Parser](#parser)
  * [Introduction](#introduction)
  * [Parsing Algorithm(s)](#parsing-algorithms)
  * [Analyzing Grammars to Find Conflicts](#analyzing-grammars-to-find-conflicts)
    * [First/First Conflicts](#firstfirst-conflicts)
    * [First/Follow Conflicts](#firstfollow-conflicts)
  * [Macros](#macros)
    * [optional](#optional)
    * [list](#list)
    * [tlist](#tlist)
    * [otlist](#otlist)
  * [Abstract Syntax Tree (AST) Transformations](#abstract-syntax-tree-ast-transformations)
    * [Why Bother With ASTs?](#why-bother-with-asts)
    * [Specifying AST Transformations](#specifying-ast-transformations)
  * [Expression Parser](#expression-parser)
    * [Introduction (Pratt parsing)](#introduction-pratt-parsing)
    * [Specifying Expression Parsers](#specifying-expression-parsers)
      * [Example: Arithmetic Expressions](#example-arithmetic-expressions)
      * [Example: Function Calls & Parenthesized Statements](#example-function-calls--parenthesized-statements)
  * [Language Targets](#language-targets)
    * [Python](#python)
    * [C](#c)
    * [Java 8](#java-8)
    * [JavaScript](#javascript)
* [Parsing Techniques](#parsing-techniques)
  * [Lexical Hints](#lexical-hints)
  * [Balancing Between Lexer and Parser](#balancing-between-lexer-and-parser)
* [Python Module Usage](#python-module-usage)
* [Cookbook](#cookbook)
  * [Parsing JSON](#parsing-json)
  * [Parsing XML](#parsing-xml)
* [Resources](#resources)
  * [Vim Syntax Highlighting](#vim-syntax-highlighting)
  * [Pygments Plugin](#pygments-plugin)

<!---toc end-->

# Introduction

Hermes is a lexer and parser generator.  Hermes attempts to make parsing easy and fun by simplifying some of the difficult aspects of parsing.

Lexical analysis is done via a context sensitive (stack-based), regex-based algorithm which allows for look-ahead at lexer time to help with common ambiguities in LL(1) rules.

Parsing is done via an [LL(1) parser](http://en.wikipedia.org/wiki/LL_parser) which generates a recursive descent parser.

Hermes makes writing these grammar rules easier by providing macros.  For example, one common pattern is to have a list of items separated by a terminal (like a list of integers separated by commas).  In vanilla LL(1) rules, this would go something like this:

```
$start = :integer + $sub | :_empty
$sub = :comma :integer $sub | :_empty
```

However, Hermes allows you to write this:

```
$start = list(:integer, :comma)
```

# Quick Start

Hermes can generate parsers in a variety of languages or be used as a Python module.  This example shows how to quickly load a grammar and start parsing.  This example is chosen for brevity because JSON is particularly easy to parse.

json.hgr
```
grammar {
  lexer {
    r'\s+' -> null
    r'\{' -> :lbrace
    r'\}' -> :rbrace
    r'\[' -> :lsquare
    r'\]' -> :rsquare
    r':' -> :colon
    r',' -> :comma
    r'true' -> :true
    r'false' -> :false
    r'null' -> :null
    r'"((?:[^"\\]|\\["\\/bfnrt]|\\u[0-9A-Fa-f]{4})*)"' -> :string
    r'-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][\+-]?[0-9]+)?' -> :number
  }
  parser {
    $value = :string | :number | $object | $array | :true | :false | :null
    $object = :lbrace list($key_value_pair, :comma) :rbrace -> Object(values=$1)
    $key_value_pair = :string :colon $value -> KeyValue(key=$0, value=$2)
    $array = :lsquare list($value, :comma) :rsquare -> Array(values=$1)
  }
}
```

Load the grammar:
```
>>> import hermes
>>> with open('json.hgr') as fp:
...     json_parser = hermes.compile(fp)
...
```

Print the parse tree:
```
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
```

Then, print out the abstract syntax tree:

```
>>> print(tree.ast().dumps(indent=2))
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
```

# Installation

Currently Hermes requires Python 3.4

Hermes can be installed via the standard `setup.py` as:

```
$ python setup.py install
```

or via [PyPi](https://pypi.python.org/pypi/hermes-parser) using pip:

```
$ pip install hermes-parser
```

# Hermes Grammar File Format

The grammar file format is a domain specific language for specifying lexer and parser rules.  The two core concepts in Hermes are Terminals and NonTerminals.

Terminals are represented as `:name` (colon followed by the name of the terminal).  These represent literal chunks of source code so they will always have attached to them the source code that they matched.  The name of a terminal is more abstract than the literal source string.

NonTerminals are represeted as `$name` (dollar sign followed by name of the nonterminal).  These represent building blocks of the language.  A nonterminal is defined to be zero or more terminals and nonterminals.

A grammar is defined with the keyword `grammar` and is enclosed in curly braces:

```
grammar {
  ...
}
```

Inside the grammar definition are definitions for a lexer and a parser

Lexer rules produce terminals and only terminals.  They are a block that starts with the keyword `lexer` and are enclosed in curly braces:

```
grammar {
  lexer {
     ...
  }
}
```

Inside the lexer definition are rules of the form:

```
r'my_regex' -> :my_token
```

The left hand side is a regular expression and the right hand side is the terminal that it produces.  See the [Lexical Analyzer](#lexical-analyzer) section for details about defining a lexical analyzer

The parser is similarly defined with the keyword `parser` and enclosed in curly braces:

```
grammar {
  lexer {
    ...
  }
  parser {
    ...
  }
}
```

The parser defines rules in the form:

```
$nonterminal = :terminal $nonterminal2 :terminal2 -> AstTranformation(t1=0, nt=1, t2=2)
```

See the [Parser](#parser) section for more details.

Each grammar has at most one lexer and exactly one parser.

# Lexical Analyzer

Lexical analysis is the first and most important step of parsing.  The goal of this stage is to walk through the source code from the beginning and identify what each element is and emit **tokens**.  A token consists of a terminal identifier, line and column numbers, and a source string that was matched.

Tokens are stringified as

```
<resource:line:col terminal "source_string_base64">
```

For example:

```
<test.source:1:10 identifier "bWFuX3BhcnNpbmdfaXNfZnVuCg==">
```

Lexer rules are regular expressions that map to terminal names.  Here are a few examples:

```
r'\+' -> :plus
r'[0-9]+' -> :integer
r'[a-zA-Z][a-zA-Z0-9_]' -> :identifier
```

Hermes attempts to make these regular expressions work [across multiple language targets](#cross-language-regexes) but sometimes specifices of the regex libraries make that not possible.  See the section on [Cross-Language Regexes](#cross-language-regexes) for more details on this.

The easiest way to get up and running and test your lexer is by using the `hermes lex` sub-command, which is described in the next section

## Example

Let's construct a simple 4-rule lexer and test it out on some source code:

lex.hgr:
```
grammar {
  lexer {
    r'\s+' -> null
    r'\+' -> :plus
    r'[0-9]+' -> :integer
    r'[a-zA-Z][a-zA-Z0-9_]*' -> :identifier
  }
}
```

This lexer matches integers, identifiers, and plus signs.  The first rule matches whitespace and tells the lexer to ignore it.  Assuming this file is saved as `lex.hgr`, we can use `hermes lex` to parse some input from stdin:

```
$ echo "foobar + 123" | hermes lex lex.hgr -
<stdin:1:1 identifier "Zm9vYmFy">
<stdin:1:8 plus "Kw==">
<stdin:1:10 integer "MTIz">
```

## Lexer Algorithm

The Lexical Analyzer works by evaluating the starting at the beginning of the string and then iterating through each lexer rule **in order**.  It tries to match the regular expresssion against the **beginning** of the string.  If it does match, it emits the necessary tokens and then advances the string pointer by the amount of characters in the full match.  Then the loop starts over.

It's important to take full advantage of the fact that lexer rules are evaluated in order.  This comes in handy in cases where you might have a `**` and a `*` operator.  Having the regex for the `**` operator first ensures that it won't match two `*` operators and never match a `**` operator.

## Specifying Lexer Rules

As mentioned before, lexer rules are essentially a regular expression that maps to a terminal.  However, Hermes allows you do much more than have one regex map to one terminal.  The most common advanced use case is to utilize capture groups in regular expressions.  For example, say I want to match a quoted string, but I don't want to save the quotes:

```
r'"([^"])"' -> :dquote_string[1]
```

The syntax `:dquote_string[1]` tells Hermes to store the first capture group in the emitted token.

Perhaps I want to emit more than one token when I match a regular expression.  This can be done by:

```
r'(foo)(bar)' -> :foobar :foo[1] :bar[2]
```

Here, three tokens are emitted.  `:foobar` which captures the entire match, and `:foo` and `:bar` which capture only their respective capture groups.

## Cross-Language Regexes

Regexes strings so far have been expressed using pythons `r''` notation.  Hermes accepts regexes expressed in double or single quotes too.  Hermes does a best-effort conversion of regexes to the target language which does work for a vast majority of cases which is why the `r''` syntax for strings is recommended

There are a few 'gotchas' with regexes that might come up, for example the regex `r'{'` will work in all languages besides Java.  To make this regex compatible for all languages simply escape it with a back-slash: `r'\{'`.  These things might be a bit difficult to debug at times, which is why Hermes also offers **Regex Enumerations** for specifying exact regexes to use for given language targets

Finally, each regex string is given to the target language via the following methods:

* Python: [regex](https://docs.python.org/3.4/library/re.html) module in standard library
* C: [libpcre2](http://www.pcre.org/)
* Java: [java.util.regex](http://docs.oracle.com/javase/7/docs/api/java/util/regex/package-summary.html).  Specifically, the parameter to [Pattern.compile()](http://docs.oracle.com/javase/7/docs/api/java/util/regex/Pattern.html#compile(java.lang.String))
* JavaScript: [RegExp()](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp) class

## Regex Enumerations & Regex Flags

Say you have a regex that is not working right in a given language target and you need your lexer to work across multiple language targets.  Regex Enumerations allow you to specify a regex in a language specific way, allowing you to specify flags to the regex library and everything.  For example, let's say I want to match a single character, even whitespace, and in a case-insensitive manner:

```
enum {
  java: "." (DOTALL, CASE_INSENSITIVE)
  python: r'.' (DOTALL, IGNORECASE)
  c: "." (PCRE_DOTALL, PCRE_CASELESS)
  javascript: "." (m, i)
} -> :char
```
## Lexer Stack

Sometimes while lexically analyzing, you might want to change state and match a different set of regular expressions until a condition is met.  Hermes offers a built-in stack to support this.  Use the syntax `@mode_name` to push a mode onto the stack and `%pop` to pop a mode off the stack and go back to where you came from.  Here is a simple lexer that only matches letters inside of parenthesis and numbers inside of square braces:

```
lexer {
  r'\s+' -> null
  r'\(' -> :lparen @letters
  r'\[' -> :lsquare @numbers
  mode<letters> {
    r'\)' -> :rparen %pop
    r'[a-zA-Z]' -> :letter
    r'\s+' -> null
  }
  mode<numbers> {
    r'\]' -> :rsquare %pop
    r'[0-9]' -> :number
    r'\s+' -> null
  }
}
```

When the lexical analysis algorithm is iterating over regular expressions, it only loops over regular expressions in the current mode.

## Regex Partials

Often times, advanced languages have regular expressions that are used many times but are very long and it can be repetative to re-type them out or copy them a bunch of times for the various lexer modes that need them.  This is where regex partials help.  A regex partial is a snippet of a regular expression that can be included in other regular expressions.  For example, the XML spec has a lengthy way that names are defined with a lot of unicode ranges for valid characters.  If we define two partials, `_NameStartChar` and `_NameChar`, they can be combined as follows:

```
lexer {
  partials {
    r'[a-zA-Z:_\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]' -> _NameStartChar
    r'[a-zA-Z0-9-\.:_\u00b7\u0300-\u036f\u203f-\u2040\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]' -> _NameChar
  }
  r'{%_NameStartChar%}({%_NameChar%})*' -> :name
}
```

The `partials {}` section defines a list of the partials.  The names must start with underscores.  To include a partial in a lexer rule use the syntax `{%_PartialName%}`.  The above regex, `r'{%_NameStartChar%}({%_NameChar%})*'`, expands to:

```
r'[a-zA-Z:_\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]([a-zA-Z0-9-\.:_\u00b7\u0300-\u036f\u203f-\u2040\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF])*'
```

## Custom Functions

Sometimes the language you are parsing requires more state or awareness than Hermes allows for natively.  Fear not!  For cases where some internal state needs to be kept, there are language-specific functions that you can call when a token is matched.

```
grammar {
  lexer {
    r'(foo)(bar)' -> :foo[1] my_func(:bar[2])
    r'\s+' -> null

    code<python> << PYTHON
    def my_func(ctx, terminal, source_string, line, col):
        default_action(ctx, terminal, source_string, line, col)
    PYTHON

    code<c> << C_CODE
    static void my_func(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col) {
        default_action(ctx, terminal, source_string, line, col);
    }
    C_CODE

    code<java> << JAVA
    public void my_func(LexerContext ctx, TerminalIdentifier terminal, String source_string, int line, int col) {
        default_action(ctx, terminal, source_string, line, col);
    }
    JAVA

    code<javascript> << JAVASCRIPT
    function my_func(ctx, terminal, source_string, line, col) {
        default_action(ctx, terminal, source_string, line, col);
    }
    JAVASCRIPT
  }
}
```

In this example, upon matching `foobar`, a `:foo` token is emitted and then the `my_func` function is called with the a `:bar` token using the second capture group.  Below the lexer rules is a section that defines the custom code in a language-dependent fashion.  The syntax uses [here document](http://en.wikipedia.org/wiki/Here_document) style syntax and the delimiters (e.g. PYTHON, C_CODE, JAVA, JAVASCRIPT) can be user-defined.

In the example above, `my_func()` essentially acts as a pass-through solely as a demonstration.  Calling `default_action()` simply emits the token that was matched.

There are two other special functions that Hermes allows for: `init()` and `destroy()`.  These functions are called before lexing begins and after it completes, respectively.  The return value from `init()` is saved in `ctx.user_context`.  Hermes won't touch this structure at all.  This is where any custom state should be stored.

Users can define the following custom lexer code:

* Function to be called upon specific token being matched (example `my_func` above)
* Default action to be called on *every* token match (overriding `default_action` above)
* `init()` function, which is called before lexing starts.  The return value is accessible via every other custom function
* `destroy()` function, which is called when lexing finishes.

Below are specifics for how to use custom functions in each language

### Python

#### init() function

```python
def init(ctx):
    # actions to take when lexer starts.
    # return an object that will be passed to each subsequent function
```

The `init` function is called exactly once before lexing begins.  The parameter is a `LexerContext` object (see below).

The return value of `init` is set as the `user_context` field on the `LexerContext` object.  This will be available to all other functions defined.

#### destroy() function

```
def destroy(ctx):
    pass
```

The `destroy` function is called exactly once when lexing completes.  The parameter is a `LexerContext` object (see below).

#### Token Match Function

Lexer functions are called on regex matches, for example:

```
r'(foo)(bar)' -> :foo[1] my_func(:bar[2])
```

`my_func` would be defined as:

```python
def my_func(ctx, terminal, source_string, line, col):
    # If this function contained only the following line of code, this is a pass-through.
    default_action(ctx, terminal, source_string, line, col)

    # Alternatively, you may emit tokens manually
    emit(ctx, terminal, source_string, line, col)

    # Alternatively, you may emit custom tokens
    emit(ctx, "foo_token", "foo", line, col)
    emit(ctx, "bar_token", "", line, col)

    # You may access the context returned from init():
    if ctx.user_context.my_var:
      emit(ctx, "baz_token", "", line, col)
```

One may also override the default action that is called whenever any token is matched by defining the `default_action` function:

```python
def default_action(ctx, terminal, source_string, line, col):
    emit(ctx, terminal, source_string, line, col)
```

* `ctx` is the `LexerContext` object.  `ctx.user_context` is the return value from `init()`
* `terminal` is the string version of the token
* `source_string` is the source code that was matched via regex
* `line` and `col` are the location in the source code where this match took place

#### LexerContext object

`LexerContext` shouldn't normally be modified by the user or even accessed, though nothing specifically precludes this.  This object contains the following properties:

```
string = "source code to lexically analyze"
resource = "where the code came from"
stack = ['default']
line = 1
col = 1
tokens = []
user_context = ... # return value from init()
```

The `destroy()` function is called when lexing completes.

### Java

#### init() function

```java
public Object init() {
    return null;
}
```

The `init` function is called exactly once before lexing begins.  The parameter is a `LexerContext` object (see below).

The return value of `init` is set as the `context` field on the `LexerContext` object.  This will be available to all other functions defined.

#### destroy() function

```java
public void destroy(Object context) {
    return;
}
```

The `destroy` function is called exactly once when lexing completes.  The parameter is a `LexerContext` object (see below).

#### Token Match Function

Lexer functions are called on regex matches, for example:

```
r'(foo)(bar)' -> :foo[1] my_func(:bar[2])
```

`my_func` could be defined as:

```java
public void my_func(LexerContext lctx, TerminalIdentifier terminal, String source_string, int line, int col) {
    emit(lctx, terminal, source_string, line, col);
}
```

Alternatively one could override the default function that's called when a token is matched by implementing `default_action`:

```java
public void default_action(LexerContext lctx, TerminalIdentifier terminal, String source_string, int line, int col) {
    emit(lctx, terminal, source_string, line, col);
}
```

#### LexerContext Object

```java
private class LexerContext {
    public String string;
    public String resource;
    public int line;
    public int col;
    public Stack<String> stack;
    public Object context;
    public List<Terminal> terminals;
}
```

### C

#### init() function

```c
static void *
init() {
    return NULL;
}
```

The `init` function is called exactly once before lexing begins.

The return value of `init` is set as the `user_context` field on the `LEXER_CONTEXT_T *` object.  This will be available to all other functions defined.

#### destroy() function

```c
static void
destroy(void * context) {
    return;
}
```

The `destroy` function is called exactly once when lexing completes.  The parameter is a `LEXER_CONTEXT_T *` object (see below).

#### Token Match Function

Lexer functions are called on regex matches, for example:

```
r'(foo)(bar)' -> :foo[1] my_func(:bar[2])
```

`my_func` could be defined as:

```c
static void
my_func(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col) {
    emit(ctx, terminal, source_string, line, col);
}
```

Alternatively one could override the default function that's called when a token is matched by implementing `default_action`:

```c
static void
default_action(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col) {
    emit(ctx, terminal, source_string, line, col);
}
```

#### LEXER_CONTEXT_T Object

```java
typedef struct lexer_context_t {
    char * string;
    char * resource;
    void * user_context;
    int * stack;    /* Stack of mode enums */
    int stack_size; /* Allocated size of 'stack' */
    int stack_top;  /* index into 'stack' */
    TOKEN_LIST_T * token_list;
    int line;
    int col;
} LEXER_CONTEXT_T;
```

### JavaScript

#### init() function

```javascript
function init() {
    return {}
}
```

The `init` function is called exactly once before lexing begins.

The return value of `init` is set as the `user_context` field on the `ctx` object.  This will be available to all other functions defined.

#### destroy() function

```javascript
function destroy(context) {
    return 0;
}
```

The `destroy` function is called exactly once when lexing completes.  The parameter is a `ctx` object (see below).

#### Token Match Function

Lexer functions are called on regex matches, for example:

```
r'(foo)(bar)' -> :foo[1] my_func(:bar[2])
```

`my_func` could be defined as:

```javascript
function my_func(ctx, terminal, source_string, line, col) {
    emit(ctx, terminal, source_string, line, col)
}
```

Alternatively one could override the default function that's called when a token is matched by implementing `default_action`:

```javascript
function default_action(ctx, terminal, source_string, line, col) {
    emit(ctx, terminal, source_string, line, col)
}
```

#### ctx Object

```javascript
ctx = {
    string: string,
    resource: resource,
    user_context: init(),
    mode_stack: ['default'],
    tokens: [],
    line: 1,
    col: 1
}
```

# Parser
## Introduction

The parser section of a Hermes grammar file defines how the sequence of tokens emitted by the lexer ought to be arranged and adds semantics to those arrangements.  The parser section defines a set of grammar rules, which are of the form:

```
$nonterminal = (:terminal | $nonterminal)+
```

This is called a rule (or production).  The left-hand side of the rule must be a non-terminal, which is preceded by a dollar sign.  The right-hand side fo the rule is a sequence of terminals and nonterminals that express how that non-terminal is expanded.

The first rule defined is the starting rule.

The output of the parser is a parse tree, though more often the actual desired output is an abstract syntax tree (see the section below).  Here is an example of a simple grammar and the output of using `hermes parse` to print out the parse tree:

ab.hgr:

```
grammar {
  lexer {
    r'a' -> :a
    r'b' -> :b
    r';' -> :semi
    r'\s+' -> null
  }
  parser {
    $start = $sub :semi
    $sub = :a $sub :b
    $sub = :_empty
  }
}
```

The starting rule is `$start = $sub :semi`.  There's a special terminal, `:_empty` which matches the empty string.  The two `$sub` rules say that non-terminal `$sub` can be either an `:a` terminal followed by a recursive call to `$sub`, followed by a `:b` terminal, OR it can be the empty string.  This grammar matches some number of `:a` terminals followed by the same number of `:b` terminals.

```
$ echo 'aaabbb;' | hermes parse ab.hgr /dev/stdin --tree
(start:
  (sub:
    <string:1:1 a "YQ==">,
    (sub:
      <string:1:2 a "YQ==">,
      (sub:
        <string:1:3 a "YQ==">,
        (sub: ),
        <string:1:4 b "Yg==">
      ),
      <string:1:5 b "Yg==">
    ),
    <string:1:6 b "Yg==">
  ),
  <string:1:7 semi "Ow==">
)
```

> **NOTE** The terminals in the parse tree are displayed using Base64 encoding because of potential newline characters that could make the tree hard to read.

## Parsing Algorithm(s)

Hermes generates parsers using the LL(1) parsing algorithm and generates a recursive descent parser.  Hermes also has support for sub-parsers that use a different algorithm for parsing expressions.  See the section on expression parsing below for more details.

Using the combination of these two parsing algorithms, and some creativity, pretty much anything is parseable.  See the later section on parsing techniques for details about how to think about parsing using the tools Hermes provides to parse your language.

## Analyzing Grammars to Find Conflicts

`hermes analyze` is a great tool for examining your grammar and figuring out what the conflicts are.

Analyzing the grammar in the previous section will not be terribly interesting other to illustrate the output of the `hermes analyze` command:

```
$ hermes analyze ab.hgr
+-----------+
| Terminals |
+-----------+

:_empty, :a, :b, :semi

+---------------+
| Non-Terminals |
+---------------+

$start, $sub

+----------------------+
| Expanded LL(1) Rules |
+----------------------+

$start = $sub :semi
$sub = :_empty
$sub = :a $sub :b

+------------+
| First sets |
+------------+

$start: {:a, :semi}
$sub: {:_empty, :a}

+-------------+
| Follow sets |
+-------------+

$start: {:_eos}
$sub: {:b, :semi}


Grammar contains no conflicts!
```

The most important pieces of this output are at the bottom where it tells you if there are any conflicts (in this case there are none), and the first/follow sets.  The first/follow sets tell you which tokens each non-terminal can start with as well as the tokens that each non-terminal can be followed with.  These are important because this is the source of LL(1) Conflicts

### First/First Conflicts

A First/First conflict is when one non-terminal has two rules which can start with the same terminal.  For example, if we modify the grammar above as follows:

```
parser {
  $start = $sub :semi
  $sub = :a $sub :b
  $sub = :a :b
  $sub = :_empty
}
```

Then `hermes analyze` will return the following conflict:

```
 -- FIRST/FIRST conflict --
Two rules for nonterminal $sub have intersecting first sets.  Can't decide which rule to choose based on terminal.

(Rule-2)  $sub = :a :b
(Rule-1)  $sub = :a $sub :b

first(Rule-2) = {:a}
first(Rule-1) = {:a}
first(Rule-2) ∩ first(Rule-1): {:a}
```

This is a conflict because when the parser trying to evaluate a `$sub` non-terminal and the next token is an `:a`, it does not know which rule to follow.

### First/Follow Conflicts

Consider the following grammar:

```
grammar {
  parser {
    $s = $a :c :b
    $a = :c
    $a = :_empty
  }
}
```

`hermes analyze` would report a first/follow conflict in this case:

```
 -- FIRST/FOLLOW conflict --
Nonterminal $a has a first and follow set that overlap.

first($a) = {:_empty, :c}
follow($a) = {:c}

first($a) ∩ follow($a) = {:c}
```

This conflict means that when parsing `$s`, since `$a` can be empty (via `$a = :_empty`), the parser does not know which path to take if a `:c` token is encountered.  Is the `:c` token because of `$a = :c` or is it because of `$a = :_empty` and the `:c` token is matched via `$s = $a :c :b`?  It's impossible to know with only one token of lookahead, so it's a conflict.

## Macros

Once you write enough language parsers, you'll realize there are two very common patterns:

* Optional things
* Lists of things

The LL(1) grammar rules for these can sometimes be tedious and require up to 4 rules to implement, which will quickly clutter one's grammar and make it hard to read.  Macros mitigate this tediousness nicely.  Here's a simple example of the `list` macro in action:

list.hgr
```
grammar {
  lexer {
    r'a' -> :a
    r'b' -> :b
    r'\s+' -> null
  }
  parser {
    $start = list($sub)
    $sub = :a | :b
  }
}
```

```
$ echo 'ababb' | hermes parse list.hgr /dev/stdin --tree
(start:
  (_gen0:
    (sub:
      <string:1:1 a "YQ==">
    ),
    (_gen0:
      (sub:
        <string:1:2 b "Yg==">
      ),
      (_gen0:
        (sub:
          <string:1:3 a "YQ==">
        ),
        (_gen0:
          (sub:
            <string:1:4 b "Yg==">
          ),
          (_gen0:
            (sub:
              <string:1:5 b "Yg==">
            ),
            (_gen0: )
          )
        )
      )
    )
  )
)
```

As you can see, there are a lot of rules that seem to have been generated for us (the ones starting with `_gen`).  Using `hermes analyze` we can see how the `list` macro was expanded into:

```
$_gen0 = $sub $_gen0
$_gen0 = :_empty
$start = $_gen0
$sub = :a
$sub = :b
```

List macros also have special meaning for abstract tree conversions.  As you can see from the parse tree above, even though all the information is present, it's in an awkward tree-structure.  If we were to convert that parse tree to an abstract syntax tree, it would look a little more workable:

```
[
  <string:1:1 a "YQ==">,
  <string:1:2 b "Yg==">,
  <string:1:3 a "YQ==">,
  <string:1:4 b "Yg==">,
  <string:1:5 b "Yg==">
]
```

Abstract syntax trees support lists as native data types, which is much more intuitive than tree representation.

### optional

This macro signifies that a particular terminal/nonterminal is optional.  `$start = optional($sub)` expands to:

```
$start = $_gen0
$_gen0 = $sub
$_gen0 = :_empty
```

### list

The `list` macro can take 1, 2, or 3 parameters:

1.  List elements, as either nonterminal or terminal
2.  Separator terminal (or null)
3.  Minimum number of elements in the list (default 0)

`$start = list($sub)` expands to:

```
$start = $_gen0
$_gen0 = $sub $_gen1
$_gen0 = :_empty
$_gen1 = $sub $_gen1
$_gen1 = :_empty
```

`$start = list($sub, :sep)` expands to:

```
$start = $_gen0
$_gen0 = $sub $_gen1
$_gen0 = :_empty
$_gen1 = :_empty
$_gen1 = :sep $sub $_gen1
```

`$start = list($sub, :sep, 4)` expands to:

```
$start = $_gen0
$_gen0 = $sub :sep $sub :sep $sub :sep $sub $_gen1
$_gen1 = :_empty
$_gen1 = :sep $sub $_gen1
```

`$start = list($sub, null, 4)` expands to:

```
$start = $_gen0
$_gen0 = $sub $sub $sub $sub $_gen1
$_gen1 = $sub $_gen1
$_gen1 = :_empty
```

### tlist

The `tlist` macro is similar to the `list` macro.  It can take 1, 2, or 3 parameters:

1.  List elements, as either nonterminal or terminal
2.  Terminator terminal (or null).  This terminator must exist after each element specified in parameter 1
3.  Minimum number of elements in the list (default 0)

Similar to the `list` macro, `tlist` creates a list of elements.  However this is slightly different from a list in that the second parameter is considered a terminator character, so it must appear after each list element.  In the example below, the list is 0-or-more list of `$sub :t`

`$start = tlist($sub, :t)` expands to:

```
$start = $_gen0
$_gen0 = $sub $_gen1
$_gen0 = :_empty
$_gen1 = :t $_gen0
```

### otlist

Same as tlist except the terminator terminal (second parameter) can be optional after the last element

`$start = otlist($sub, :t)` expands to:

```
$start = $_gen0
$_gen0 = $sub $_gen1
$_gen0 = :_empty
$_gen1 = :_empty
$_gen1 = :t $_gen2
$_gen2 = $sub $_gen1
$_gen2 = :_empty
```

## Abstract Syntax Tree (AST) Transformations

So far the primary data structure that we've been working with is the parse tree.  Parse trees contain all the important structure, and theoretically one could operate on a parse tree directly without converting it to an AST at all.  However, parse trees tend to be more bloated than they need to be for a few reasons:

1)  They contain separator characters, like curly braces and parenthesis which are vestigual once the parse tree is created.
2)  Certain data structures are represented very oddly, namely lists.
3)  Parse trees lack some semantics that would make them easier to reason about.

For these reasons, it is not recommended that clients work with parse trees and instead operate on Abstract Syntax Trees.

ASTs are the process of converting parse trees to a new type of object which resembles a class: it contains a name, and named attributes.  An AST is still a tree because AST attributes can contain either terminals or other ASTs.

### Why Bother With ASTs?

Here's one example of a parse tree generated by a `list` macro:

```
(start:
  (_gen0:
    (sub:
      <string:1:1 a "YQ==">
    ),
    (_gen0:
      (sub:
        <string:1:2 b "Yg==">
      ),
      (_gen0:
        (sub:
          <string:1:3 a "YQ==">
        ),
        (_gen0:
          (sub:
            <string:1:4 b "Yg==">
          ),
          (_gen0:
            (sub:
              <string:1:5 b "Yg==">
            ),
            (_gen0: )
          )
        )
      )
    )
  )
)
```

This is not nearly as workable as the AST transformation of this tree:

```
[
  <string:1:1 a "YQ==">,
  <string:1:2 b "Yg==">,
  <string:1:3 a "YQ==">,
  <string:1:4 b "Yg==">,
  <string:1:5 b "Yg==">
]
```

ASTs are meant to transform a parse tree into a data structure that's more usable for algorithms

### Specifying AST Transformations

Each grammar rule can specify how to transform the resulting parse tree into an abstract syntax tree.  For example:

```
grammar {
  lexer {
    r'\s+' -> null
    r'import' -> :import
    r'"[^"]+"' -> :string
    r'as' -> :as
    r'[a-zA-Z]+' -> :identifier
  }
  parser {
    $import = :import :string optional($import_namespace) -> Import(uri=$1, namespace=$2)
    $import_namespace = :as :identifier -> $1
  }
}
```

Given the string `import "foo" as bar`, the abstract syntax tree that's produced is:

```
$ echo 'import "foo" as bar' | hermes parse import.hgr /dev/stdin
(Import:
  uri=<string:1:8 string "ImZvbyI=">,
  namespace=<string:1:17 identifier "YmFy">
)
```

AST transformations always follow a grammar rule using the `->` operator.  To the right of the `->` either specifies what kind of object is created by the transformation or what part of the rule to return as the AST.

In the example above, the rule `$import = :import :string optional($import_namespace) -> Import(uri=$1, namespace=$2)` specifies that the AST object that's created is called `Import` and has two attributes: uri and namespace.  `uri=$1` means that the value for the uri attribute is the second (because it's zero-based) element in the rule which is the `:string`.

In the next rule, `$import_namespace = :as :identifier -> $1`, the AST transformation specifies that only the second morpheme, then `:identifier` should be returned as the AST for this rule.

## Expression Parser

Parsing expressions with top-down one-token-lookahead parsing is an exercise in futility.  Anybody attempting to do this will quickly be inundated with left recursion and unable to produce a working grammar.  Luckily, there's a better way to handle this, using a sub-parser that's meant for parsing expressions.

### Introduction (Pratt parsing)

The algorithm for parsing expressions is a different algorithm than the standard recursive descent parser.  The expression parsing algorithm was first developed by Vaughan R. Pratt in his [1973 paper](http://tdop.github.io/).  The algorithm uses a table of operator precedences to establish what to do in cases of ambiguity.  This algorithm works surprisingly well for all kinds of expressions and it is a great compliment to LL(1) parsing

### Specifying Expression Parsers



#### Example: Arithmetic Expressions
#### Example: Function Calls & Parenthesized Statements

## Language Targets
### Python
### C
### Java 8
### JavaScript

# Parsing Techniques
## Lexical Hints
## Balancing Between Lexer and Parser
# Python Module Usage
# Cookbook
## Parsing JSON
## Parsing XML
# Resources
## Vim Syntax Highlighting
## Pygments Plugin
