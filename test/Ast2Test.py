import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class Ast2Test(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/ast2.zgr', 'START')

  def test_firstSets(self):
    self.assertFirst({
      'start': {'identifier', 'ε', 'sub', 'n', 'for', 's', 'λ'},
      'statement': {'n', 'for', 'identifier', 's', 'sub', 'λ'},
      'tmp1': {'semi', 'ε'},
      'expr': {'identifier', 'sub', 'n', 's', 'λ'},
      'for': {'for'},
      'tmp0': {'for', 'identifier', 'ε', 's', 'n', 'sub', 'λ'},
      'forsub': {'identifier', 'ε', 'sub', 'n', 's', 'λ'},
      'forbody': {'identifier', 'ε', 's', 'n', 'for', 'sub', 'λ'}
    })
    
  def test_followSets(self):
    self.assertFollow({
      'start': {'σ'},
      'expr': {'div', 'add', 'eq', 'mul', 'semi', 'σ', 'sub', 'rparen'},
      'statement': {'semi', 'σ'},
      'for': {'semi', 'σ'},
      'tmp0': {'σ'},
      'forsub': {'semi', 'rparen'},
      'tmp1': {'σ'},
      'forbody': {'rbrace'}
    })

  def test_conflicts(self):
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_codeGeneration(self):
    self.runWithTokens(['identifier','eq','identifier','eq','n','semi','for','lparen','identifier','eq','n','semi','semi','identifier','eq','s','add','n','rparen','lbrace','identifier','eq','n','add','identifier','mul','n','div','s','semi','rbrace','semi','identifier','add','identifier']) \
        .assertParseTree('(start: (tmp0: (statement: (eq: identifier, (eq: identifier, n))), (tmp1: semi, (statement: (for: for, lparen, (forsub: (eq: identifier, n)), semi, (forsub: ), semi, (forsub: (eq: identifier, (add: s, n))), rparen, lbrace, (forbody: (statement: (eq: identifier, (add: n, (mul: identifier, (div: n, s))))), semi, (forbody: )), rbrace)), (tmp1: semi, (statement: (add: identifier, identifier)), (tmp1: )))))') \
        .assertAst('(Program: statements=[(Assign: rhs=(Assign: rhs=n, lhs=identifier), lhs=identifier), (For: decl=(Assign: rhs=n, lhs=identifier), body=(Assign: rhs=(Add: rhs=(Multiply: rhs=(Divide: rhs=s, lhs=n), lhs=identifier), lhs=n), lhs=identifier), cond=None, iter=(Assign: rhs=(Add: rhs=n, lhs=s), lhs=identifier)), (Add: rhs=identifier, lhs=identifier)])')

  # Same as test_codeGeneration but the last 'semi' was removed
  def test_codeGenerationWithError(self):
    self.runWithTokens(['identifier','eq','identifier','eq','n','semi','for','lparen','identifier','eq','n','semi','semi','identifier','eq','s','add','n','rparen','lbrace','identifier','eq','n','add','identifier','mul','n','div','s','semi','rbrace','identifier','add','identifier']) \
        .assertParseTree('Syntax Error: Finished parsing without consuming all tokens.')
if __name__ == '__main__':
  unittest.main()
