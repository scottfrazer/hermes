import unittest, os, subprocess, re, json, imp, tempfile, shutil
from pkg_resources import resource_filename
from hashlib import sha224
from random import random
from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory
from hermes.GrammarCodeGenerator import FactoryFactory as TemplateFactoryFactory
from hermes.GrammarCodeGenerator import TemplateWriter
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

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    tree = getParseTree(self.grammar, self.testCaseDir)
    self.assertEqual(self.expected, tree, 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesPythonAbstractSyntaxTreeTest(HermesTest):

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def runTest(self):
    self.assertEqual(self.expected, getAst(self.grammar, self.testCaseDir), 'expected ASTs to match (test %s)' % (self.testCaseDir))

class HermesJavaTest(HermesTest):
  def runJavaParser(self, grammar, testCaseDir, arg):
    tmpDir = tempfile.mkdtemp()
    shutil.copy(os.path.join(testCaseDir, 'tokens'), tmpDir)
    shutil.copytree(os.path.join(testCaseDir, '..', 'javacp', 'org'), os.path.join(tmpDir, 'org'))
    templateFactory = TemplateFactoryFactory().create('java')
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write([grammar], tmpDir, addMain=True)

    javaSourceFiles = list(filter(lambda filename: filename.endswith('.java'), os.listdir(tmpDir)))

    try:
      compileCmd = 'javac *.java 2>/dev/null'
      subprocess.check_call(compileCmd, cwd=tmpDir, shell=True, stderr=None)
    except subprocess.CalledProcessError as error:
      print('FAILED TO COMPILE', testCaseDir)
      shutil.rmtree(tmpDir)
      return error.output.decode('utf-8').strip()

    try:
      runCmd = 'java ParserMain grammar {type} 2>&1 <tokens'.format(type=arg)
      return subprocess.check_output(runCmd, shell=True, stderr=None, cwd=tmpDir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmpDir)

class HermesJavaParseTreeTest(HermesJavaTest):

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def getJavaParseTree(self):
    return self.runJavaParser(self.grammar, self.testCaseDir, 'parsetree')

  def runTest(self):
    self.assertEqual(self.expected, self.getJavaParseTree(), 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesJavaAbstractSyntaxTreeTest(HermesJavaTest):

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def getJavaAst(self):
    return self.runJavaParser(self.grammar, self.testCaseDir, 'ast')

  def runTest(self):
    self.assertEqual(self.expected, self.getJavaAst(), 'expected ASTs to match (test %s)' % (self.testCaseDir))

class HermesCTest(HermesTest):
  def runCParser(self, grammar, testCaseDir, arg):
    tmpDir = tempfile.mkdtemp()
    shutil.copy(os.path.join(testCaseDir, 'tokens'), tmpDir)
    templateFactory = TemplateFactoryFactory().create('c')
    templateWriter = TemplateWriter(templateFactory)
    templateWriter.write([grammar], tmpDir, addMain=True)

    cSourceFiles = list(filter(lambda x: x.endswith('.c'), os.listdir(tmpDir)))

    try:
      compileCmd = 'gcc -o parser {sources} -g -Wall -pedantic -ansi -std=c99 2>/dev/null'.format(sources=' '.join(cSourceFiles))
      subprocess.check_call(compileCmd, cwd=tmpDir, shell=True, stderr=None)
    except subprocess.CalledProcessError as error:
      shutil.rmtree(tmpDir)
      return error.output.decode('utf-8').strip()

    try:
      runCmd = './parser grammar {type} < tokens'.format(type=arg)
      return subprocess.check_output(runCmd, shell=True, stderr=None, cwd=tmpDir).decode('utf-8').strip()
    except subprocess.CalledProcessError as exception:
      return exception.output.decode('utf-8').strip()
    finally:
      shutil.rmtree(tmpDir)

class HermesCParseTreeTest(HermesCTest):

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def getCParseTree(self):
    return self.runCParser(self.grammar, self.testCaseDir, 'parsetree')

  def runTest(self):
    tree = self.getCParseTree()
    self.assertEqual(self.expected, tree, 'expected parse trees to match (test %s)' % (self.testCaseDir))

class HermesCAbstractSyntaxTreeTest(HermesCTest):

  def __init__(self, testCaseDir=None, grammar=None, expected=None):
    super().__init__()
    self.__dict__.update(locals())
    self.maxDiff = None

  def getCAst(self):
    return self.runCParser(self.grammar, self.testCaseDir, 'ast')

  def runTest(self):
    self.assertEqual(self.expected, self.getCAst(), 'expected ASTs to match (test %s)' % (self.testCaseDir))

def getParseTree(grammar, testCaseDir):
  tmpDir = tempfile.mkdtemp()
  shutil.copy(os.path.join(testCaseDir, 'tokens'), tmpDir)

  templateFactory = TemplateFactoryFactory().create('python')
  templateWriter = TemplateWriter(templateFactory)
  templateWriter.write([grammar], tmpDir, addMain=True)

  try:
    runCmd = 'python ParserMain.py grammar parsetree < tokens 2>&1'
    return subprocess.check_output(runCmd, shell=True, stderr=None, cwd=tmpDir).decode('utf-8').strip()
  except subprocess.CalledProcessError as exception:
    return exception.output.decode('utf-8').strip()
  finally:
    shutil.rmtree(tmpDir)

def getAst(grammar, testCaseDir):
  tmpDir = tempfile.mkdtemp()
  shutil.copy(os.path.join(testCaseDir, 'tokens'), tmpDir)

  templateFactory = TemplateFactoryFactory().create('python')
  templateWriter = TemplateWriter(templateFactory)
  templateWriter.write([grammar], tmpDir, addMain=True)

  try:
    runCmd = 'python ParserMain.py grammar ast < tokens 2>&1'
    return subprocess.check_output(runCmd, shell=True, stderr=None, cwd=tmpDir).decode('utf-8').strip()
  except subprocess.CalledProcessError as exception:
    return exception.output.decode('utf-8').strip()
  finally:
    shutil.rmtree(tmpDir)

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
    grammar = grammarParser.parse_new( 'grammar', open(grammarFile) )

    path = os.path.join(testDirectory, 'parsetree')
    if os.path.exists(path):
      expectedParseTree = open(path).read().strip()
      if len(expectedParseTree):
        suite.addTest(HermesPythonParseTreeTest(testDirectory, grammar, expectedParseTree))
        suite.addTest(HermesCParseTreeTest(testDirectory, grammar, expectedParseTree))
        suite.addTest(HermesJavaParseTreeTest(testDirectory, grammar, expectedParseTree))
    else:
      fp = open(path, 'w')
      fp.write(getParseTree(grammar, testDirectory))
      fp.close()
      print('generated %s' % (path))

    path = os.path.join(testDirectory, 'ast')
    if os.path.exists(path):
      expectedAst = open(path).read().strip()
      suite.addTest(HermesPythonAbstractSyntaxTreeTest(testDirectory, grammar, expectedAst))
      suite.addTest(HermesCAbstractSyntaxTreeTest(testDirectory, grammar, expectedAst))
      suite.addTest(HermesJavaAbstractSyntaxTreeTest(testDirectory, grammar, expectedAst))
    else:
      fp = open(path, 'w')
      fp.write(getAst(grammar, testDirectory))
      fp.close()
      print('generated %s' % (path))


  for grammarTest in os.listdir(grammarTestsDirectory):
    try:
      int(grammarTest)
    except ValueError:
      continue
    testDirectory = os.path.join(grammarTestsDirectory, grammarTest)
    grammarParser = GrammarFileParser(HermesParserFactory().create())
    grammar = grammarParser.parse_new( 'grammar', open(os.path.join(testDirectory, 'grammar.zgr')) )
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
        expected = json.loads(contents)
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
