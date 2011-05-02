import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class Ast1Test(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/ast1.zgr', 'START')

  def test_firstSets(self):
    self.assertFirst({
      'start': {'sub', 'identifier', 'n', 's', 'ε', 'for', 'λ'},
      'assignstatementsub': {'sub', 'identifier', 'n', 's', 'λ'},
      'statement': {'identifier', 'sub', 'n', 'for', 's', 'λ'},
      'tmp0': {'sub', 'identifier', 'n', 's', 'ε', 'for', 'λ'},
      'tmp1': {'ε', 'comma'},
      'expr': {'sub', 'n', 's', 'λ'},
      'fordeclstatement': {'sub', 'identifier', 'n', 'ε', 's', 'λ'},
      'complexexpression': {'sub', 'identifier', 'n', 's', 'λ'},
      'forcondstatement': {'sub', 'n', 'ε', 's', 'λ'},
      'foriterstatement': {'sub', 'identifier', 'n', 'ε', 's', 'λ'},
      'forbody': {'sub', 'identifier', 'n', 's', 'ε', 'for', 'λ'},
      'assignstatement': {'identifier'},
      'forstatement': {'for'}
    })
    
  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      'tmp1': {'σ'},
      'forbody': {'rbrace'},
      'assignstatement': {'semi', 'comma', 'rparen', 'σ'},
      'assignstatementsub': {'semi', 'σ', 'comma', 'rparen'},
      'fordeclstatement': {'semi'},
      'complexexpression': {'semi', 'rparen'},
      'tmp0': {'σ'},
      'forstatement': {'semi', 'comma', 'σ'},
      'statement': {'semi', 'comma', 'σ'},
      'foriterstatement': {'rparen'},
      'expr': {'sub', 'σ', 'div', 'semi', 'mul', 'add', 'rparen', 'comma'},
      'forcondstatement': {'semi'},
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens(['identifier','eq','identifier','eq','n','comma','for','lparen','identifier','eq','n','semi','semi','identifier','eq','s','add','n','rparen','lbrace','identifier','eq','n','add','s','mul','n','div','s','semi','rbrace']) \
        .assertParseTree('(start: (tmp0: (statement: (assignstatement: identifier, eq, (assignstatementsub: (assignstatement: identifier, eq, (assignstatementsub: n))))), (tmp1: comma, (statement: (forstatement: for, lparen, (fordeclstatement: (complexexpression: (assignstatement: identifier, eq, (assignstatementsub: n)))), semi, (forcondstatement: ), semi, (foriterstatement: (complexexpression: (assignstatement: identifier, eq, (assignstatementsub: (add: s, n))))), rparen, lbrace, (forbody: (statement: (assignstatement: identifier, eq, (assignstatementsub: (add: n, (mul: s, (div: n, s)))))), semi, (forbody: )), rbrace)), (tmp1: ))))') \
        .assertAst('(Program: statements=[(Assign: var=identifier, val=(Assign: var=identifier, val=n)), (For: decl=(Assign: var=identifier, val=n), body=(Assign: var=identifier, val=(Add: rhs=(Multiply: rhs=(Divide: rhs=s, lhs=n), lhs=s), lhs=n)), cond=None, iter=(Assign: var=identifier, val=(Add: rhs=n, lhs=s)))])')

if __name__ == '__main__':
  unittest.main()
