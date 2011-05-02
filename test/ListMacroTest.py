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
      'tmp0': {'ε', 'a', 'b'}
    })

  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      'item': {'rparen', 'b', 'a'},
      'tmp0': {'rparen'}
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")
  
  def test_listFirstFollowConflicts(self):
    self.loadGrammarFile('grammars/list1.zgr', 'START')
    self.assertEqual(1, len(self.grammar.conflicts), "Expected one list first/follow conflict")

  def test_codeGeneration(self):
    self.runWithTokens( ['lparen','a','b','rparen'] ).assertParseTree( '(start: lparen, (tmp0: (item: a), (tmp0: (item: b), (tmp0: ))), rparen)' )
  
  def test_codeGeneration2(self):
    self.loadGrammarFile('grammars/list2.zgr', 'START') \
        .runWithTokens( ['function','identifier','lparen','param1','comma','param2','rparen','lbrace','a','b','a','b','rbrace','class','identifier','lbrace','private','x','public','y','rbrace'] ) \
        .assertParseTree( '(start: (tmp0: (statement: (funcdef: function, identifier, lparen, (tmp1: (param: param1), (tmp2: comma, (param: param2), (tmp2: ))), rparen, lbrace, (tmp0: (statement: a), (tmp0: (statement: b), (tmp0: (statement: a), (tmp0: (statement: b), (tmp0: ))))), rbrace)), (tmp0: (statement: (classdef: class, identifier, lbrace, (tmp3: (class_statement: private, (class_atom: x)), (tmp3: (class_statement: public, (class_atom: y)), (tmp3: ))), rbrace)), (tmp0: ))))' )

if __name__ == '__main__':
  unittest.main()
