import unittest, os, subprocess, re, json, imp
from hashlib import sha224
from random import random
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from hermes.GrammarCodeGenerator import PythonTemplate
from hermes.Morpheme import NonTerminal

directory = 'test/cases'

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

class HermesParseTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.expected, getParseTree(self.grammar, self.tokens), 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesAbstractSyntaxTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, tokens=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.expected, getAst(self.grammar, self.tokens), 'expected ASTs to match (test %s)' % (self.testCaseDir))

def getParseTree(grammar, tokens):
  parser = getParser(grammar)
  terminals = list(map(lambda x: hermesparser.Terminal(parser.str_terminal[x]), tokens))
  try:
    parsetree = parser.parse(terminals)
  except hermesparser.SyntaxError as error:
    return str(error)
  return str(parsetree)

def getAst(grammar, tokens):
  parser = getParser(grammar)
  terminals = list(map(lambda x: hermesparser.Terminal(parser.str_terminal[x]), tokens))
  try:
    ast = parser.parse(terminals).toAst()
  except hermesparser.SyntaxError as error:
    return str(error)
  astPrettyPrint = hermesparser.AstPrettyPrintable(ast)
  if isinstance(astPrettyPrint, list):
    return '[%s]' % (', '.join([str(x) for x in ast]))
  else:
    return str(astPrettyPrint)

def getParser(grammar):
  global hermesparser
  template = PythonTemplate()
  code = template.render(grammar)
  modulename = 'hermesparser' #sha224( str(random()).encode('ascii') ).hexdigest()[:25]
  fullpath = modulename + '.py'
  fp = open(fullpath, 'w')
  fp.write(code)
  fp.close()
  os.remove('__pycache__/hermesparser.cpython-32.pyc')
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
        suite.addTest(HermesParseTreeTest(testDirectory, grammar, tokens, expectedParseTree))
    else:
      fp = open(path, 'w')
      fp.write(getParseTree(grammar, tokens))
      fp.close()
      print('generated %s' % (path))

    path = os.path.join(testDirectory, 'ast')
    if os.path.exists(path):
      expectedAst = open(path).read().strip()
      if len(expectedAst):
        suite.addTest(HermesAbstractSyntaxTreeTest(testDirectory, grammar, tokens, expectedAst))
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
