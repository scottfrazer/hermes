import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class ExprGrammarTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/expr.zgr', 'START')

  def test_firstSets(self):
    self.assertFirst({
      'start': {'lparen', 'lbrace', 'subtract', 'lsquare', 'b', 'identifier', 'a', 'number', 'λ'},
      'sub': {'lparen', 'lbrace', 'subtract', 'lsquare', 'identifier', 'b', 'number', 'a', 'λ'},
      '_gen0': {'lbrace', 'lsquare', 'b', 'identifier', 'number', 'subtract', 'lparen', 'ε', 'a', 'λ'},
      '_gen1': {'comma', 'ε'},
      '_gen2': {'lbrace', 'lsquare', 'subtract', 'identifier', 'number', 'ε', 'lparen', 'λ'},
      '_gen3': {'comma', 'ε'},
      'item': {'b', 'a'},
      'expr': {'lbrace', 'lsquare', 'identifier', 'subtract', 'lparen', 'number', 'λ'},
    })
    
  def test_followSets(self):
    self.assertFollow({
      'start': set(['σ']),
      'sub': set(['comma', 'σ']),
      'item': set(['σ', 'comma']),
      'expr': set(['divide', 'rparen', 'subtract', 'σ', 'comma', 'add', 'multiply']),
      '_gen0': set(['σ']),
      '_gen1': set(['σ'])
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.loadGrammarFile('grammars/expr.zgr', 'START') \
        .runWithTokens(['a','comma','b','comma','number','add','number']) \
        .assertParseTree("(start: (_gen0: (sub: (item: a)), (_gen1: comma, (sub: (item: b)), (_gen1: comma, (sub: (add: number, number)), (_gen1: )))))")

if __name__ == '__main__':
  unittest.main()
