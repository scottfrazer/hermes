import unittest, os, sys, io, subprocess, json
from hashlib import sha224
from random import random
sys.path.append('..')

from hermes.GrammarFileParser import GrammarFileParser, HermesParserFactory, HermesParser
from hermes.Grammar import Grammar
from hermes.GrammarCodeGenerator import PythonTemplate
from hermes.Macro import LL1ListMacro
from hermes.Morpheme import Terminal, NonTerminal

class GrammarTest(unittest.TestCase):
  def loadGrammarFile( self, filename, start = None ):
    return self.loadGrammar( open(filename), start )

  def loadGrammarJson( self, j, start = None ):
    return self.loadGrammar( io.StringIO(json.dumps(j)), start )

  def loadGrammarStr( self, string, start = None ):
    return self.loadGrammar( io.StringIO(string), start )
  
  def loadGrammar( self, file_obj, start = None ):
    factory = HermesParserFactory()
    fp = GrammarFileParser( factory.create() )
    self.grammar = fp.parse( file_obj, start )
    return self

  def assertFirst( self, first ):
    for nonterminal, firstSet in first.items():
      s1 = {self.grammar.getTerminal(e) for e in firstSet}
      s2 = self.grammar.first[self.grammar.getNonTerminal(nonterminal)]
      if s1.issuperset(s2):
        diff = s1.difference(s2)
      else:
        diff = s2.difference(s1)
      self.assertEqual(s1, s2, "Incorrect first set for nonterminal %s  (expected: %s) (actual: %s) (diff: %s)"%(nonterminal, ', '.join([str(e) for e in s1]), ', '.join([str(e) for e in s2]), ', '.join([str(e) for e in diff])))
    return self

  def assertFollow( self, follow ):
    for nonterminal, followSet in follow.items():
      s1 = {self.grammar.getTerminal(e) for e in followSet}
      s2 = self.grammar.follow[self.grammar.getNonTerminal(nonterminal)]
      if s1.issuperset(s2):
        diff = s1.difference(s2)
      else:
        diff = s2.difference(s1)
      self.assertEqual(s1, s2, "Incorrect follow set for nonterminal %s  (expected: %s) (actual: %s) (diff: %s)"%(nonterminal, ', '.join([str(e) for e in s1]), ', '.join([str(e) for e in s2]), ', '.join([str(e) for e in diff])))
    return self

  def runWithTokens(self, tokens):
    tokens = [str(t) for t in tokens]
    template = PythonTemplate()
    code = template.render(self.grammar, addMain=True, initialTerminals=tokens)
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
    self.assertEqual( self.parsetree.lower(), parsetree.lower(), "Expecting parse trees to be equal")
    return self
  
  def assertAst( self, ast ):
    self.assertEqual( self.ast.lower(), ast.lower(), "Expecting ASTs to be equal")
    return self
