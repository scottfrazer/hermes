import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class Ast1Test(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/ast1.zgr', 'START')

  def test_firstSets(self):
    self.assertFirst({
      'start': {'sub', 'identifier', 'n', 's', 'ε', 'for', '_expr'},
      'assignstatementsub': {'sub', 'identifier', 'n', 's', '_expr'},
      'statement': {'identifier', 'sub', 'n', 'for', 's', '_expr'},
      '_gen0': {'sub', 'identifier', 'n', 's', 'ε', 'for', '_expr'},
      '_gen1': {'ε', 'comma'},
      '_expr': {'sub', 'n', 's', '_expr'},
      'fordeclstatement': {'sub', 'identifier', 'n', 'ε', 's', '_expr'},
      'complexexpression': {'sub', 'identifier', 'n', 's', '_expr'},
      'forcondstatement': {'sub', 'n', 'ε', 's', '_expr'},
      'foriterstatement': {'sub', 'identifier', 'n', 'ε', 's', '_expr'},
      'forbody': {'sub', 'identifier', 'n', 's', 'ε', 'for', '_expr'},
      'assignstatement': {'identifier'},
      'forstatement': {'for'}
    })
    
  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      '_gen1': {'σ'},
      'forbody': {'rbrace'},
      'assignstatement': {'semi', 'comma', 'rparen', 'σ'},
      'assignstatementsub': {'semi', 'σ', 'comma', 'rparen'},
      'fordeclstatement': {'semi'},
      'complexexpression': {'semi', 'rparen'},
      '_gen0': {'σ'},
      'forstatement': {'semi', 'comma', 'σ'},
      'statement': {'semi', 'comma', 'σ'},
      'foriterstatement': {'rparen'},
      '_expr': {'σ', 'semi', 'rparen', 'comma'},
      'forcondstatement': {'semi'},
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens(['identifier','eq','identifier','eq','n','comma','for','lparen','identifier','eq','n','semi','semi','identifier','eq','s','add','n','rparen','lbrace','identifier','eq','n','add','s','mul','n','div','s','semi','rbrace']) \
        .assertParseTree('(start: (_gen0: (statement: (assignstatement: identifier, eq, (assignstatementsub: (assignstatement: identifier, eq, (assignstatementsub: n))))), (_gen1: comma, (statement: (forstatement: for, lparen, (fordeclstatement: (complexexpression: (assignstatement: identifier, eq, (assignstatementsub: n)))), semi, (forcondstatement: ), semi, (foriterstatement: (complexexpression: (assignstatement: identifier, eq, (assignstatementsub: (_expr: s, add, n))))), rparen, lbrace, (forbody: (statement: (assignstatement: identifier, eq, (assignstatementsub: (_expr: n, add, (_expr: (_expr: s, mul, n), div, s))))), semi, (forbody: )), rbrace)), (_gen1: ))))') \
        .assertAst('(Program: statements=[(Assign: var=identifier, val=(Assign: var=identifier, val=n)), (For: decl=(Assign: var=identifier, val=n), body=(Assign: var=identifier, val=(Add: rhs=(Divide: rhs=s, lhs=(Multiply: rhs=n, lhs=s)), lhs=n)), cond=None, iter=(Assign: var=identifier, val=(Add: rhs=n, lhs=s)))])')

if __name__ == '__main__':
  unittest.main()
