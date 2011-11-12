import unittest, os, subprocess, re, json
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

  def __init__(self, testCaseDir=None, expected=None, actual=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.actual, self.expected, 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesAbstractSyntaxTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, expected=None, actual=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.actual, self.expected, 'expected ASTs to match (test %s)' % (self.testCaseDir))

def run(grammar, tokens):
  tokens = [str(t) for t in tokens]
  template = PythonTemplate()
  code = template.render(grammar, addMain=True, initialTerminals=tokens)
  filename = sha224( str(random()).encode('ascii') ).hexdigest()[:25] + '.py'
  fullpath = '/tmp/' + filename
  fp = open(fullpath, 'w')
  fp.write(code)
  fp.close()
  parsetree = subprocess.check_output(['python', fullpath, 'parsetree']).decode('utf-8').strip()
  ast = subprocess.check_output(['python', fullpath, 'ast']).decode('utf-8').strip()
  os.remove(fullpath)
  return (parsetree, ast)

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
    grammarParser = GrammarFileParser(HermesParserFactory().create())
    grammar = grammarParser.parse( open(os.path.join(testDirectory, 'grammar.zgr')) )
    tokens = list(filter(lambda x: x, open(os.path.join(testDirectory, 'tokens')).read().split('\n')))
    (parsetree, ast) = run(grammar, tokens)

    path = os.path.join(testDirectory, 'parsetree')
    if os.path.exists(path):
      expectedParseTree = open(path).read().strip()
      if len(expectedParseTree):
        suite.addTest(HermesParseTreeTest(testDirectory, parsetree, expectedParseTree))
    else:
      fp = open(path, 'w')
      fp.write(parsetree)
      fp.close()
      print('generated %s/parsetree' % (path))

    path = os.path.join(testDirectory, 'ast')
    if os.path.exists(path):
      expectedAst = open(path).read().strip()
      if len(expectedAst):
        suite.addTest(HermesAbstractSyntaxTreeTest(testDirectory, ast, expectedAst))
    else:
      fp = open(path, 'w')
      fp.write(ast)
      fp.close()
      print('generated %s/ast' % (path))


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
