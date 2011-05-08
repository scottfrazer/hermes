import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class AstTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/ast.zgr', 'start')

  def test_firstSets(self):
    self.assertFirst({
      'expr': {'a', 'b', 'sub', 'λ'},
      '_gen1': {'comma', 'ε'},
      '_gen0': {'ε', 'identifier', 'a', 'b', 'sub', 'λ'},
      'assignstatement': {'identifier'},
      'start': {'ε', 'identifier', 'a', 'b', 'sub', 'λ'},
      'statements': {'identifier', 'a', 'b', 'sub', 'λ'},
    })
    
  def test_followSets(self):
    self.assertFollow({
      'expr': {'comma', 'σ', 'div', 'mul', 'add', 'sub'},
      '_gen1': {'σ'},
      '_gen0': {'σ'},
      'assignstatement': {'comma', 'σ'},
      'start': {'σ'},
      'statements': {'comma', 'σ'},
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens(['a','add','b','comma','identifier','eq','a','sub','b','mul','a']) \
        .assertParseTree('(start: (_gen0: (statements: (expr: a, add, b)), (_gen1: comma, (statements: (assignstatement: identifier, eq, (expr: a, sub, (expr: b, mul, a)))), (_gen1: ))))') \
        .assertAst('(Program: statements=[(Add: rhs=b, lhs=a), (Assign: var=identifier, val=(Subtract: rhs=(Multiply: rhs=a, lhs=b), lhs=a))])')

if __name__ == '__main__':
  unittest.main()
