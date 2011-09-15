import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class Expr2GrammarTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/expr2.zgr', 'START')

  def test_firstSets(self):
    self.assertFirst({
      'type_name': {'int', 'char'},
      'initializer_list_item': {'item'},
      '_gen2': {},
      'sub': {'λ', 'lsquare', 'lparen', 'a', 'subtract', 'identifier', 'lparen_cast', 'lbrace', 'b', 'number'},
      '_gen3': {},
      '_expr': {'λ', 'lsquare', 'lparen_cast', 'subtract', 'identifier', 'lparen', 'lbrace', 'number'},
      '_gen1': {'comma', 'ε'},
      '_gen4': {},
      'comma_opt': {'comma', 'ε'},
      '_gen5': {},
      'item': {'b', 'a'},
      'start': {'λ', 'lsquare', 'lparen', 'a', 'subtract', 'identifier', 'lparen_cast', 'lbrace', 'b', 'number'},
      '_gen0': {'λ', 'lsquare', 'lparen', 'ε', 'subtract', 'a', 'identifier', 'lparen_cast', 'lbrace', 'b', 'number'}
    })
    
  def test_followSets(self):
    self.assertFollow({
      'type_name': {},
      'initializer_list_item': {},
      '_gen2': {},
      'sub': {'comma', 'σ'},
      '_gen3': {},
      '_expr': {'comma', 'σ', 'rparen'},
      '_gen1': {'σ'},
      '_gen4': {},
      'comma_opt': {},
      '_gen5': {},
      'item': {'comma', 'σ'},
      'start': {'σ'},
      '_gen0': {'σ'},
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.loadGrammarFile('grammars/expr2.zgr', 'start') \
        .runWithTokens(['lparen_cast','int','rparen','lbrace','item','rbrace']) \
        .assertParseTree("(start: (_gen0: (sub: (_expr: (_expr: lparen_cast, (type_name: int), rparen), lbrace, (_gen4: (initializer_list_item: item), (_gen5: )), (comma_opt: ), rbrace)), (_gen1: )))") \
        .assertAst('[(TypeInitializion: type=int, initializer=[item])]')

if __name__ == '__main__':
  unittest.main()
