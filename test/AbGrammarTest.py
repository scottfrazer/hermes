import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class AbGrammarTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/ab.zgr', 'start')
  
  def test_firstSets(self):
    self.assertFirst({
      'start': {'a', 'semi'},
      'sub': {'a', 'ε'}
    })
  
  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      'sub': {'semi', 'b'}
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens( ['a','a','b','b','semi'] ) \
        .assertParseTree( '(start: (sub: a, (sub: a, (sub: ), b), b), semi)' )

  def test_codeGeneration1(self):
    self.runWithTokens( ['a','b','semi'] ).assertParseTree( '(start: (sub: a, (sub: ), b), semi)' )

  def test_codeGeneration2(self):
    self.runWithTokens( ['a','a','a','b','semi'] ).assertParseTree( 'Unexpected symbol.  Expected b, got semi.' )

  def test_codeGeneration3(self):
    self.runWithTokens( ['semi'] ).assertParseTree( '(start: (sub: ), semi)' )

  def test_codeGeneration4(self):
    self.runWithTokens( ['a'] ).assertParseTree( 'Unexpected symbol.  Expected b, got None.' )

  def test_codeGeneration5(self):
    self.runWithTokens( [] ).assertParseTree( '' )

  def test_codeGeneration6(self):
    self.runWithTokens( [14] ).assertParseTree( 'Parser instance has no attribute \'TERMINAL_14\'' )

if __name__ == '__main__':
  unittest.main()
