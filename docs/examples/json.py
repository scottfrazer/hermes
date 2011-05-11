import sys, re, pprint
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
      
if len(sys.argv) < 2:
  print("missing JSON file(s)")
  sys.exit(-1)

for filename in sys.argv[1:]:
  try:
    lexer = JsonLexer(open(filename).read())
    tree = JsonParser.parse( lexer, 'object' )
    compiler = JsonToPythonCompiler()
    object = compiler.compile( tree.toAst() )
    print('%s is valid JSON:\n' % filename)
    print(object)
  except Exception as e:
    print('Error:', e)