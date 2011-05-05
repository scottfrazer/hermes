import sys, traceback

sym = None

class Tree():
  def __init__(self, name):
    self.children = []
    self.name = name
  def add( self, tree ):
    self.children.append( tree )
  def __str__( self ):
    children = []
    for child in self.children:
      if isinstance(child, list):
        children.append('[' + ', '.join([str(a) for a in child]) + ']')
      else:
        children.append(str(child))
    return self.name + ': [' + ', '.join(children) + ']'

class SyntaxError:
  def __init__(self, tok):
    self.tok = tok
  def __str__(self):
    return "Parser Error: Unexpected token %s" % (self.tok)

class UnexpectedEndOfFile:
  def __init__(self, ExpectedTerminalsSet, TerminalStr):
    self.ExpectedTerminalsSet = ExpectedTerminalsSet
    self.TerminalStr = TerminalStr
  def __str__(self):
    return "Parse Error: Unexpected EOF."

%%DECL_TERMINALS%%

%%DECL_NONTERMINALS%%

%%INIT%%

class TokenRecorder:
  def __init__(self):
    self.stack = []
    self.awake = False
  def wake(self):
    self.awake = True
    self.stack = []
    return self
  def sleep(self):
    self.awake = False
    return self
  def record(self, s):
    self.stack.append(sym)
    return self
  def tokens(self):
    return self.stack
    
recorder = TokenRecorder()

def rewind(recorder):
  global tokens
  tokens = recorder.tokens().append(tokens)

def getsym():
  global sym, nTerminals
  if len(tokens):
    nextTok = tokens.pop()
    if nextTok >= nTerminals or nextTok < 0:
      return SyntaxError(nextTok)
    else:
      sym = nextTok
      if recorder.awake:
        recorder.record(sym)
      return sym
  sym = None

def _getstr(r):
  return TerminalStr[r]

def expect(s):
  global sym
  str = _getstr(s)
  r = accept(s)

  if type(r) is SyntaxError:
    return r

  if r == True:
    return str

  # Syntax Error
  if sym != None:
    str = _getstr(sym)
    return SyntaxError(str)
  else:
    return UnexpectedEndOfFile(str, TerminalStr)

def get_rule(N):
  index = getNonterminalParseTableIndex(N)
  return ParseTable[index][sym]

def accept(s):
  global sym
  if s == sym:
    r = getsym()
    if type(r) is SyntaxError:
      return r
    return True
  return False

def getBindingPower(sym):
  try:
    return BindingPower[sym]
  except KeyError:
    return 0

def hasSyntaxError(tree):
  for t in tree.children:
    if type(t) is SyntaxError or type(t) is UnexpectedEndOfFile:
      return t
  return None

def EXPR( rbp = 0 ):
  t = sym
  left = nud()
  while rbp < getBindingPower(sym):
    left = led(left)
  return left

%%PARSER%%
%%AST%%
%%PUBLIC_FUNCTION_DEFINITIONS%%
%%MAIN%%