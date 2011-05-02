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
      'tmp1': {'comma', 'ε'},
      'tmp0': {'ε', 'identifier', 'a', 'b', 'sub', 'λ'},
      'assignstatement': {'identifier'},
      'start': {'ε', 'identifier', 'a', 'b', 'sub', 'λ'},
      'statements': {'identifier', 'a', 'b', 'sub', 'λ'},
    })
    
  def test_followSets(self):
    self.assertFollow({
      'expr': {'comma', 'σ', 'div', 'mul', 'add', 'sub'},
      'tmp1': {'σ'},
      'tmp0': {'σ'},
      'assignstatement': {'comma', 'σ'},
      'start': {'σ'},
      'statements': {'comma', 'σ'},
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens(['a','add','b','comma','identifier','eq','a','sub','b','mul','a']) \
        .assertParseTree('(start: (tmp0: (statements: (add: a, b)), (tmp1: comma, (statements: (assignstatement: identifier, eq, (sub: a, (mul: b, a)))), (tmp1: ))))') \
        .assertAst('(Program: statements=[(Add: rhs=b, lhs=a), (Assign: var=identifier, val=(Subtract: rhs=(Multiply: rhs=a, lhs=b), lhs=a))])')

if __name__ == '__main__':
  unittest.main()
