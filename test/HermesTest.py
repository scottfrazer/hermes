import unittest, os, subprocess, re

directory = 'test/cases'

class HermesFirstSetTest(unittest.TestCase):

  def __init__(self, arg=None, expected=None, actual=None):
    super().__init__(arg)
    self.__dict__.update(locals())
    self.maxDiff = None

  def test_areTheFirstSetsCorrect(self):
    self.assertEqual(self.actual, self.expected)

class HermesFollowSetTest(unittest.TestCase):

  def __init__(self, arg=None, expected=None, actual=None):
    super().__init__(arg)
    self.__dict__.update(locals())
    self.maxDiff = None

  def test_areTheFollowSetsCorrect(self):
    self.assertEqual(self.actual, self.expected)

class HermesParseTest(unittest.TestCase):

  def __init__(self, arg=None, filepath=None):
    super().__init__(arg)
    self.__dict__.update(locals())
    self.maxDiff = None

  def test_parseTree(self):
    filepath = os.path.join(directory, self.filepath)
    self.assertEqual(self.getGccOutput(filepath), self.getCastOutput(filepath), \
        "File %s didn't parse the same in GCC and cAST" % (filepath) )

class HermesAbstractSyntaxTreeTest(unittest.TestCase):

  def __init__(self, arg=None, filepath=None):
    super().__init__(arg)
    self.__dict__.update(locals())
    self.maxDiff = None

  def test_abstractSyntaxTree(self):
    filepath = os.path.join(directory, self.filepath)
    self.assertEqual(self.getGccOutput(filepath), self.getCastOutput(filepath), \
        "File %s didn't parse the same in GCC and cAST" % (filepath) )

def load_tests(loader, tests, pattern):
  files = os.listdir(os.path.join(directory, 'grammar'))
  suite = unittest.TestSuite()
  for path in files:
    suite.addTest(CastVersusGccTest('test_doesCastPreprocessExactlyLikeGccDoes', path))
    for (extension, transformFunction) in transformations:
      expectedPath = os.path.join(directory, path + '.' + extension)
      sourcePath = os.path.join(directory, path)
      sourcecode = SourceCode(path, open(sourcePath))
      actual = transformFunction(sourcecode)
      if not os.path.exists(expectedPath):
        fp = open(expectedPath, 'w')
        fp.write(actual)
        fp.close()
      expected = open(expectedPath).read()
      suite.addTest( CastTest('test_isCorrect', expected, actual) )
  return suite
