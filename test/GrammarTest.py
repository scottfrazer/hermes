import unittest, os, sys, io
import subprocess
from hashlib import sha224
from random import random
sys.path.append('..')

from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from hermes.GrammarCodeGenerator import GrammarCodeGenerator, Resources, PythonTemplate

class GrammarTest(unittest.TestCase):
  def loadGrammarFile( self, filename, start = None ):
    fp = GrammarFileParser()
    self.grammar = fp.parse( open(filename) , start )
    return self
  
  def loadGrammarStr( self, string, start = None ):
    fp = GrammarFileParser()
    self.grammar = fp.parse( io.StringIO(string) , start )
    return self
  
  def assertFirst( self, first ):
    for nonterminal, firstSet in first.items():
      s1 = {self.grammar.terminals[e] for e in firstSet}
      s2 = self.grammar.first[self.grammar.nonterminals[nonterminal]]
      self.assertEqual(s1, s2, "Expecting first sets to be equal.  (expected: %s) (actual: %s)"%(', '.join([str(e) for e in s1]), ', '.join([str(e) for e in s2])))
    return self

  def assertFollow( self, follow ):
    for nonterminal, followSet in follow.items():
      s1 = {self.grammar.terminals[e] for e in followSet}
      s2 = self.grammar.follow[self.grammar.nonterminals[nonterminal]]
      self.assertEqual(s1, s2, "Expecting follow sets to be equal.  (expected: %s) (actual: %s)"%(', '.join([str(e) for e in s1]), ', '.join([str(e) for e in s2])))
    return self

  def runWithTokens(self, tokens):
    tokens = [str(t) for t in tokens]
    resources = Resources(self.grammar, tokens, True )
    template = PythonTemplate(resources)
    code = template.render()
    filename = sha224( str(random()).encode('ascii') ).hexdigest()[:25] + '.py'
    fullpath = '/tmp/' + filename
    fp = open(fullpath, 'w')
    fp.write(code)
    fp.close()
    self.parsetree = subprocess.check_output(['python', fullpath, 'parsetree']).decode('utf-8').strip()
    self.ast = subprocess.check_output(['python', fullpath, 'ast']).decode('utf-8').strip()
    os.remove(fullpath)
    return self
  
  def assertParseTree( self, parsetree ):
    self.assertEqual( self.parsetree, parsetree, "Expecting parse trees to be equal")
    return self
  
  def assertAst( self, ast ):
    self.assertEqual( self.ast, ast, "Expecting ASTs to be equal")
    return self
