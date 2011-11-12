import unittest, os, subprocess, re, json
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
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

class HermesParseTest:
  pass

class HermesAbstractSyntaxTreeTest:
  pass

def load_tests(loader, tests, pattern):
  testsDirectory = os.path.join(directory, 'grammar')
  suite = unittest.TestSuite()
  jsonifySets = lambda arg:'{\n%s\n}' % (',\n'.join(['  "%s": [%s]' % (nt, ', '.join(['"'+z+'"' for z in theSet])) for nt, theSet in arg.items()]))
  for grammarTest in os.listdir(testsDirectory):
    try:
      int(grammarTest)
    except ValueError:
      continue
    testDirectory = os.path.join(testsDirectory, grammarTest)
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
