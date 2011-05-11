Parsing JSON
============

Parsing JSON is a relatively simple task.  The entire JSON specification is right on the json.org homepage!  To start, we need a fairly straightforward grammar for parsing JSON:

.. code-block:: javascript

    {
      "ll1": {
        "start": "object",
        "rules": [
          "object := 'lbrace' + list(name_value_pair, 'comma') + 'rbrace' -> Object( attributes=$1 )",
          "array := 'lsquare' + list(value, 'comma') + 'rsquare' -> Array( items=$1 )",
          "value := object | array | 'string' | 'number' | 'true' | 'false' | 'null'",
          "name_value_pair := 'string' + 'colon' + value -> NameValuePair( name=$0, value=$2 )"
        ]
      }
    }

We're assuming that the lexical analyzer has the capability to match the format of strings and numbers.  To build out a full JSON lexer, I've constructed an iterable class called JsonLexer which checks if any of the list of regular expressions matches the beginning of the string.  If so, return a new JsonToken object with the correct terminal id.  If not, we have an error.

.. code-block:: python

    import JsonParser
    from JsonParser import Parser

    class JsonToken(JsonParser.Terminal):
      def __init__( self, id, string, lineno, colno):
        self.id = id
        self.string = string
        self.lineno = lineno
        self.colno = colno
      def __str__( self ):
        return Parser.terminal_str[self.id]

    class JsonLexer():
      regex = [
        (r'\s+', None), # ignore whitespace
        (r'\{', Parser.TERMINAL_LBRACE),
        (r'\}', Parser.TERMINAL_RBRACE),
        (r'\[', Parser.TERMINAL_LSQUARE),
        (r'\]', Parser.TERMINAL_RSQUARE),
        (r',', Parser.TERMINAL_COMMA),
        (r':', Parser.TERMINAL_COLON),
        (r'"(([^"\\]|\\[\\"/bfnrt]|\\u\d{4})*)"', Parser.TERMINAL_STRING),
        (r'-?([1-9][0-9]+|0)(\.[0-9]+)?([eE][+-]?[0-9]+)?', Parser.TERMINAL_NUMBER),
        (r'true', Parser.TERMINAL_TRUE),
        (r'false', Parser.TERMINAL_FALSE),
        (r'null', Parser.TERMINAL_NULL),
      ]
      def __init__(self, jsonString):
        self.jsonString = jsonString
        self.colno = 1
        self.lineno = 1
      def __iter__(self):
        return self
      def next(self):
        return self.__next__()
      def advance(self, i):
        self.jsonString = self.jsonString[i:]
        if len(self.jsonString) <= 0:
          raise StopIteration()
      def __next__(self):
        if len(self.jsonString) <= 0:
          raise StopIteration()
        for (pattern, terminal) in self.regex:
          match = re.match(pattern, self.jsonString)
          if match:
            token = JsonToken(terminal, match.group(0), self.lineno, self.colno)
            self.advance( len(match.group(0)) )
            newlines = len(list(filter(lambda x: x == '\n', match.group(0))))
            self.lineno += newlines
            if newlines > 0:
              self.colno = len(match.group(0).split('\n')[-1])
            else:
              self.colno += len(match.group(0))
            if terminal != None:
              return token
        raise Exception('Invalid character on line %d, col %d: %s' % (self.lineno, self.colno, self.jsonString[:100].replace('\n', '\\n')))

To test this out, we can print each token in a JSON file.  Since the grammar specification is a JSON file, we'll use that!

.. code-block:: python

    >>> lexer = JsonLexer(open('json.zgr').read())
    >>> for token in lexer:
    ...   print(token)
    ...
    lbrace
    string
    colon
    lbrace
    string
    colon
    string
    comma
    string
    colon
    lsquare
    string
    comma
    string
    comma
    string
    comma
    string
    rsquare
    rbrace
    rbrace

Since the parser only needs an iterable and a starting point, we need nothing more to get an Ast object:

.. code-block:: python

  >>> import JsonParser
  >>> lexer = JsonLexer(open('json.zgr').read())
  >>> parser = JsonParser.Parser()
  >>> print( parser.parse( lexer, 'object' ).toAst() )
  (Object: attributes=[(NameValuePair: name=string, value=(Object: attributes=[(NameValuePair: name=string, value=string), (NameValuePair: name=string, value=(Array: items=[string, string, string, string]))]))])

We could further process this AST and compile it into native Python objects (dictionaries, list, etc) by writing a function that walks the AST and converts each node to its python equivalent.  To do this, I've implemented a compiler class that takes an AST as input and returns a python type:

.. code-block:: python

  class JsonToPythonCompiler:
    def compile(self, ast):
      if isinstance(ast, JsonParser.Ast):
        if ast.name == 'Object':
          return dict(list(map(lambda x: self.compile(x), ast.getAttr('attributes'))))
        elif ast.name == 'Array':
          return list(map(lambda x: self.compile(x), ast.getAttr('items')))
        elif ast.name == 'NameValuePair':
          return (self.compile(ast.getAttr('name')), self.compile(ast.getAttr('value')))
      elif isinstance(ast, JsonToken):
        if ast.id == Parser.TERMINAL_STRING:
          return ast.string.replace('"', '')
        if ast.id == Parser.TERMINAL_NUMBER:
          return float(ast.string)
        if ast.id == Parser.TERMINAL_TRUE:
          return True
        if ast.id == Parser.TERMINAL_FALSE:
          return False
        if ast.id == Parser.TERMINAL_NULL:
          return None
      else:
        print("AST %s is not a valid type" % (ast))

Now all the code is in place to do a full compilation to native python types.  Let's try it out!

.. code-block:: python

  >>> import JsonParser
  >>> lexer = JsonLexer(open('json.zgr').read())
  >>> parser = JsonParser.Parser()
  >>> compiler = JsonToPythonCompiler()
  >>> ast = parser.parse( lexer, 'object' ).toAst()
  >>> object = compiler.compile( ast )
  >>> print(object)
  {'ll1': {'rules': ["object := 'lbrace' + list(name_value_pair, 'comma') + 'rbrace' -> Object( attributes=$1 )", "array := 'lsquare' + list(value, 'comma') + 'rsquare' -> Array( items=$1 )", "value := object | array | 'string' | 'number' | 'true' | 'false' | 'null'", "name_value_pair := 'string' + 'colon' + value -> NameValuePair( name=$0, value=$2 )"], 'start': 'object'}}
