import unittest, os, subprocess, re, json, imp
from hashlib import sha224
from random import random
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from hermes.GrammarCodeGenerator import PythonTemplate, CHeaderTemplate, CSourceTemplate
from hermes.Morpheme import NonTerminal

directory = 'test/cases'

class terminal:
  def __init__(self, id, string):
    self.__dict__.update(locals())

class token:
  def __init__(self, terminal, lineno=0, colno=0, source_string=''):
    self.__dict__.update(locals())

class HermesTest(unittest.TestCase):
  pass

class HermesFirstSetTest(HermesTest):

  def __init__(self, testCaseDir=None, nonterminal=None, expected=None, actual=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.actual, self.expected, \
        'First set for nonterminal %s in test %s does not match expected value\n\nexpected: %s\nactual:%s' % ( self.nonterminal, self.testCaseDir, self.expected, self.actual))

class HermesFollowSetTest(HermesTest):

  def __init__(self, testCaseDir=None, nonterminal=None, expected=None, actual=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.actual, self.expected, \
        'Follow set for nonterminal %s in test %s does not match expected value\n\nexpected: %s\nactual:%s' % ( self.nonterminal, self.testCaseDir, self.expected, self.actual))

class HermesConflictTest(HermesTest):

  def __init__(self, testCaseDir=None, nonterminal=None, expected=None, actual=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.actual, self.expected, 'expected conflicts to match')

class HermesPythonParseTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    tree = getParseTree(self.grammar, self.tokens)
    self.assertEqual(self.expected, tree, 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesPythonAbstractSyntaxTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.expected, getAst(self.grammar, self.tokens), 'expected ASTs to match (test %s)' % (self.testCaseDir))

class HermesCParseTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None
    self.tokens = None
    if tokens:
      self.tokens = list(map(lambda x: token(terminal(grammar.getTerminal(x), x)), tokens))

  def runTest(self):
    tree = getCParseTree(self.grammar, self.tokens)
    self.assertEqual(self.expected, tree, 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesCAbstractSyntaxTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None
    self.tokens = None
    if tokens:
      self.tokens = list(map(lambda x: token(terminal(grammar.getTerminal(x), x)), tokens))

  def runTest(self):
    self.assertEqual(self.expected, getCAst(self.grammar, self.tokens), 'expected ASTs to match (test %s)' % (self.testCaseDir))

def getParseTree(grammar, tokens):
  parser = getParser(grammar)
  terminals = hermesparser.TokenStream(list(map(lambda x: hermesparser.Terminal(parser.terminals[x]), tokens)))
  try:
    parsetree = parser.parse(terminals)
  except hermesparser.SyntaxError as error:
    return str(error)
  parsetreePrettyPrint = hermesparser.ParseTreePrettyPrintable(parsetree)
  return str(parsetreePrettyPrint)

def getAst(grammar, tokens):
  parser = getParser(grammar)
  terminals = hermesparser.TokenStream(list(map(lambda x: hermesparser.Terminal(parser.terminals[x]), tokens)))
  try:
    ast = parser.parse(terminals).toAst()
  except hermesparser.SyntaxError as error:
    return str(error)
  astPrettyPrint = hermesparser.AstPrettyPrintable(ast)
  return str(astPrettyPrint)

def getCParseTree(grammar, tokens):
  return runCParser(grammar, tokens, 'parsetree')

def getCAst(grammar, tokens):
  return runCParser(grammar, tokens, 'ast')

def runCParser(grammar, tokens, arg):
  hash = sha224( str(random()).encode('ascii') ).hexdigest()[:10]
  for (outfile, renderer) in [('parser.h', CHeaderTemplate()), ('parser.c', CSourceTemplate())]:
    fullpath = outfile
    code = renderer.render(grammar, addMain=True, initialTokens=tokens)
    fp = open(fullpath, 'w')
    fp.write(code)
    fp.close()

  subprocess.check_call('gcc -std=c99 -g -o parser parser.c 2>/dev/null', shell=True, stderr=None)

  output = ''
  try:
    output = subprocess.check_output('./parser ' + arg, shell=True, stderr=None)
  except subprocess.CalledProcessError as exception:
    output = exception.output
  subprocess.check_call('rm parser.h parser.c parser', shell=True, stderr=None)
  return output.decode('ascii').strip()

def getParser(grammar):
  global hermesparser
  template = PythonTemplate()
  code = template.render(grammar)
  modulename = 'hermesparser' #
  fullpath = modulename + '.py'
  fp = open(fullpath, 'w')
  fp.write(code)
  fp.close()
  try:
    os.remove('__pycache__/hermesparser.cpython-32.pyc')
  except OSError:
    pass
  hermesparser = imp.load_source('hermesparser', 'hermesparser.py')
  parser = hermesparser.Parser()
  os.remove(fullpath)
  return parser

def load_tests(loader, tests, pattern):
  grammarTestsDirectory = os.path.join(directory, 'grammar')
  parsingTestsDirectory = os.path.join(directory, 'parsing')
  suite = unittest.TestSuite()
  jsonifySets = lambda arg:'{\n%s\n}' % (',\n'.join(['  "%s": [%s]' % (nt, ', '.join(['"'+z+'"' for z in theSet])) for nt, theSet in arg.items()]))
  for parsingTest in os.listdir(parsingTestsDirectory):
    try:
      int(parsingTest)
    except ValueError:
      continue
    testDirectory = os.path.join(parsingTestsDirectory, parsingTest)
    grammarFile = os.path.join(testDirectory, 'grammar.zgr')
    tokensFile = os.path.join(testDirectory, 'tokens')
    grammarParser = GrammarFileParser(HermesParserFactory().create())
    grammar = grammarParser.parse( open(grammarFile) )
    tokens = list(filter(lambda x: x, open(tokensFile).read().split('\n')))

    path = os.path.join(testDirectory, 'parsetree')
    if os.path.exists(path):
      expectedParseTree = open(path).read().strip()
      if len(expectedParseTree):
        suite.addTest(HermesPythonParseTreeTest(testDirectory, grammar, tokens, expectedParseTree))
        suite.addTest(HermesCParseTreeTest(testDirectory, grammar, tokens, expectedParseTree))
    else:
      fp = open(path, 'w')
      fp.write(getParseTree(grammar, tokens))
      fp.close()
      print('generated %s' % (path))

    path = os.path.join(testDirectory, 'ast')
    if os.path.exists(path):
      expectedAst = open(path).read().strip()
      suite.addTest(HermesPythonAbstractSyntaxTreeTest(testDirectory, grammar, tokens, expectedAst))
      suite.addTest(HermesCAbstractSyntaxTreeTest(testDirectory, grammar, tokens, expectedAst))
    else:
      fp = open(path, 'w')
      fp.write(getAst(grammar, tokens))
      fp.close()
      print('generated %s' % (path))


  for grammarTest in os.listdir(grammarTestsDirectory):
    try:
      int(grammarTest)
    except ValueError:
      continue
    testDirectory = os.path.join(grammarTestsDirectory, grammarTest)
    grammarParser = GrammarFileParser(HermesParserFactory().create())
    grammar = grammarParser.parse( open(os.path.join(testDirectory, 'grammar.zgr')) )
    grammarFirst = dict()
    for k,v in grammar.first.items():
      if isinstance(k, NonTerminal):
        grammarFirst[k.string] = set(map(lambda x: x.string, v))
    grammarFollow = dict()
    for k,v in grammar.follow.items():
      if isinstance(k, NonTerminal):
        grammarFollow[k.string] = set(map(lambda x: x.string, v))

    path = os.path.join(testDirectory, 'conflicts.json')
    if os.path.exists(path):
      contents = open(path).read()
      if len(contents):
        for k,v in expected.items():
          suite.addTest(HermesConflictTest(testDirectory, k, contents, '\n'.join([x.toJson() for x in grammar.conflicts])))
    else:
      if len(grammar.conflicts):
        fp = open(path, 'w')
        fp.write('\n'.join([x.toJson() for x in grammar.conflicts]))
        fp.close()
      else:
        fp = open(path, 'w')
        fp.close()
      print('generated %s/conflicts.json (%d conflicts)' % (path, len(grammar.conflicts)))

    path = os.path.join(testDirectory, 'first.json')
    if os.path.exists(path):
      contents = open(path).read()
      if len(contents):
        expected = json.loads(contents)
        for k,v in expected.items():
          suite.addTest(HermesFirstSetTest(testDirectory, k, set(expected[k]), grammarFirst[k]))
    else:
      if len(grammar.conflicts):
        fp = open(path, 'w')
        fp.close()
        print('generated %s/first.json (empty file because of conflicts)' % (path))
      else:
        for k,v in grammarFirst.items():
          grammarFirst[k] = list(v)
        fp = open(path, 'w')
        fp.write(jsonifySets(grammarFirst))
        fp.close()
        print('generated %s/first.json' % (path))

    path = os.path.join(testDirectory, 'follow.json')
    if os.path.exists(path):
      contents = open(path).read()
      if len(contents):
        expected = json.loads(contents)
        for k,v in expected.items():
          suite.addTest(HermesFollowSetTest(testDirectory, k, set(expected[k]), grammarFollow[k]))
    else:
      if len(grammar.conflicts):
        fp = open(path, 'w')
        fp.close()
        print('generated %s/follow.json (empty file because of conflicts)' % (path))
      else:
        for k,v in grammarFollow.items():
          grammarFollow[k] = list(v)
        fp = open(path, 'w')
        fp.write(jsonifySets(grammarFollow))
        fp.close()
        print('generated %s/follow.json' % (path))

  return suite
