import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from GrammarTest import GrammarTest

class Pl0GrammarTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/pl0.zgr', 'PROGRAM')
  
  def test_firstSets(self):
    self.assertFirst({
      'factor': set(['ident', 'lparen', 'number']),
      'term_sub1': set(['times', 'divide', 'ε']),
      'block_proc': set(['procedure', 'ε']),
      'condition': set(['ident', 'plus', 'number', 'odd', 'minus', 'lparen']),
      'unary_add_op': set(['minus', 'ε', 'plus']),
      'program': set(['ident', 'call', 'const', 'begin', 'var', 'while', 'procedure', 'if']),
      'block_var1': set(['comma', 'ε']),
      'expression_sub1': set(['minus', 'ε', 'plus']),
      'mul_op': set(['times', 'divide']),
      'add_op': set(['minus', 'plus']),
      'block': set(['ident', 'call', 'begin', 'const', 'var', 'while', 'procedure', 'if']),
      'block_const': set(['const', 'ε']),
      'block_var': set(['var', 'ε']),
      'op': set(['lt', 'gteq', 'pound', 'equal', 'gt', 'lteq']),
      'statement': set(['begin', 'if', 'ident', 'while', 'call']),
      'ident': set(['ident']),
      'expression': set(['ident', 'number', 'plus', 'lparen', 'minus']),
      'number': set(['number']),
      'block_const1': set(['comma', 'ε']),
      'term': set(['ident', 'lparen', 'number']),
      'statement_sub1': set(['semi', 'ε'])
    })
  
  def test_followSets(self):
    self.assertFollow({
      'term_sub1': set(['gteq', 'then', 'plus', 'pound', 'minus', 'equal', 'do', 'lt', 'lteq', 'rparen', 'semi', 'dot', 'gt', 'end']),
      'block_const1': set(['var']),
      'statement': set(['dot', 'semi', 'end']),
      'op': set(['plus', 'minus', 'number', 'lparen', 'ident']),
      'mul_op': set(['gteq', 'then', 'plus', 'pound', 'equal', 'minus', 'do', 'lt', 'times', 'lteq', 'rparen', 'semi', 'dot', 'divide', 'gt', 'end']),
      'factor': set(['gteq', 'then', 'plus', 'pound', 'equal', 'minus', 'do', 'lt', 'times', 'lteq', 'rparen', 'semi', 'dot', 'divide', 'gt', 'end']),
      'condition': set(['then', 'do']),
      'block_proc': set(['if', 'while', 'ident', 'call', 'begin']),
      'block_const': set(['var']),
      'block': set(['dot', 'semi']),
      'block_var1': set(['semi']),
      'block_var': set(['procedure']),
      'number': set(['gteq', 'then', 'plus', 'var', 'equal', 'minus', 'semi', 'lt', 'times', 'lteq', 'rparen', 'do', 'dot', 'divide', 'gt', 'end', 'comma', 'pound']),
      'ident': set(['gteq', 'then', 'plus', 'assign', 'minus', 'equal', 'semi', 'lt', 'times', 'lteq', 'rparen', 'do', 'dot', 'comma', 'divide', 'gt', 'end', 'pound']),
      'expression': set(['lt', 'semi', 'gteq', 'then', 'lteq', 'dot', 'pound', 'gt', 'rparen', 'equal', 'end', 'do']),
      'program': set(['σ']),
      'term': set(['gteq', 'then', 'plus', 'pound', 'equal', 'minus', 'do', 'lt', 'lteq', 'rparen', 'semi', 'dot', 'gt', 'end']),
      'add_op': set(['ident', 'gteq', 'then', 'plus', 'number', 'pound', 'equal', 'minus', 'do', 'lt', 'lteq', 'rparen', 'semi', 'dot', 'lparen', 'gt', 'end']),
      'unary_add_op': set(['ident', 'lparen', 'number']),
      'expression_sub1': set(['lt', 'semi', 'gteq', 'then', 'rparen', 'lteq', 'dot', 'pound', 'equal', 'gt', 'end', 'do']),
      'statement_sub1': set(['end']),
    })
  
  def test_conflicts(self):
    self.assertEqual([], self.grammar.conflicts, "Expected zero conflicts")
  
  def test_codeGeneration1(self):
    self.loadGrammarFile( 'grammars/pl0.zgr', 'PROGRAM' ) \
        .runWithTokens( ['const','ident','equal','number','comma','ident','equal','number','var','ident','comma','ident','semi','call','ident','dot'] ) \
        .assertParseTree("(program: (block: (block_const: const, (ident: ident), equal, (number: number), (block_const1: comma, (ident: ident), equal, (number: number))), (block_var: var, (ident: ident), (block_var1: comma, (ident: ident)), semi), (block_proc: ), (statement: call, (ident: ident))), dot)")
  
  def test_codeGeneration(self):
     self.runWithTokens( ['var','ident','semi','ident','assign','number','dot'] ) \
        .assertParseTree("(program: (block: (block_const: ), (block_var: var, (ident: ident), (block_var1: ), semi), (block_proc: ), (statement: (ident: ident), assign, (expression: (unary_add_op: ), (term: (factor: (number: number)), (term_sub1: )), (expression_sub1: )))), dot)")
  

if __name__ == '__main__':
  unittest.main()
