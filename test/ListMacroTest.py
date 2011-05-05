import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class ListMacroTest(GrammarTest):

  def setUp(self):
    self.loadGrammarFile('grammars/list.zgr', 'START')
  
  def test_firstSets(self):
    self.assertFirst({
      'start': {'lparen'},
      'item': {'a', 'b'},
      '_gen0': {'ε', 'a', 'b'}
    })

  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      'item': {'rparen', 'b', 'a'},
      '_gen0': {'rparen'}
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")
  
  def test_listFirstFollowConflicts(self):
    self.loadGrammarFile('grammars/list1.zgr', 'START')
    self.assertEqual(1, len(self.grammar.conflicts), "Expected one list first/follow conflict")

  def test_codeGeneration(self):
    self.runWithTokens( ['lparen','a','b','rparen'] ).assertParseTree( '(start: lparen, (_gen0: (item: a), (_gen0: (item: b), (_gen0: ))), rparen)' )
  
  def test_codeGeneration2(self):
    self.loadGrammarFile('grammars/list2.zgr', 'START') \
        .runWithTokens( ['function','identifier','lparen','param1','comma','param2','rparen','lbrace','a','b','a','b','rbrace','class','identifier','lbrace','private','x','public','y','rbrace'] ) \
        .assertParseTree( '(start: (_gen0: (statement: (funcdef: function, identifier, lparen, (_gen1: (param: param1), (_gen2: comma, (param: param2), (_gen2: ))), rparen, lbrace, (_gen0: (statement: a), (_gen0: (statement: b), (_gen0: (statement: a), (_gen0: (statement: b), (_gen0: ))))), rbrace)), (_gen0: (statement: (classdef: class, identifier, lbrace, (_gen3: (class_statement: private, (class_atom: x)), (_gen3: (class_statement: public, (class_atom: y)), (_gen3: ))), rbrace)), (_gen0: ))))' )

if __name__ == '__main__':
  unittest.main()
