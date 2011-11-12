import unittest
from hermes.GrammarFileParser import HermesParserFactory
from hermes.Morpheme import Terminal, NonTerminal
from hermes.Grammar import AstSpecification, AstTranslation

class ExprRuleParserTest(unittest.TestCase):
  def setUp(self):
    self.parser = HermesParserFactory().getExprRuleParser()

  def assertProduction(self, expected, production):
    self.assertEqual(expected, list(map(lambda x: (x.string, type(x)), production.morphemes)))

  def assertAstSpecification(self, name, expected, ast):
    self.assertEqual(AstSpecification, type(ast))
    self.assertEqual(name, ast.name)
    self.assertEqual(expected, list(map(lambda x: (str(x[0]), str(x[1])), ast.parameters.items())))

  def assertAstTranslation(self, index, ast):
    self.assertEqual(AstTranslation, type(ast))
    self.assertEqual(index, ast.idx)

  def test_one(self):
    rules = self.parser.parse("expr := {'a' + b -> NudAst( x=$1 )} + {'c' + d} -> Ast( y=$0 )")
    self.assertProduction([('a', Terminal), ('b', NonTerminal)], rules[0].nudProduction)
    self.assertProduction([('c', Terminal), ('d', NonTerminal)], rules[0].ledProduction)
    self.assertAstSpecification('NudAst', [('x', '1')], rules[0].nudAst)
    self.assertAstSpecification('Ast', [('y', '0')], rules[0].ast)

  def test_two(self):
    rules = self.parser.parse("expr := {'a' + 'b'} + {'c' + d}")
    self.assertProduction([('a', Terminal), ('b', Terminal)], rules[0].nudProduction)
    self.assertProduction([('c', Terminal), ('d', NonTerminal)], rules[0].ledProduction)
    self.assertAstTranslation(0, rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

  def test_three(self):
    rules = self.parser.parse("expr := {'a' + 'b' -> $1} + {'c' + d} -> $$")
    self.assertProduction([('a', Terminal), ('b', Terminal)], rules[0].nudProduction)
    self.assertProduction([('c', Terminal), ('d', NonTerminal)], rules[0].ledProduction)
    self.assertAstTranslation(1, rules[0].nudAst)
    self.assertAstTranslation('$', rules[0].ast)

  def test_four(self):
    rules = self.parser.parse("expr := {'a' + 'b' -> NudAst( x=$0 )} + {'c' + d} -> $$")
    self.assertProduction([('a', Terminal), ('b', Terminal)], rules[0].nudProduction)
    self.assertProduction([('c', Terminal), ('d', NonTerminal)], rules[0].ledProduction)
    self.assertAstSpecification('NudAst', [('x', '0')], rules[0].nudAst)
    self.assertAstTranslation('$', rules[0].ast)

  def test_four(self):
    rules = self.parser.parse("expr := {'a' + 'b' -> NudAst()} + {'c' + d} -> Ast()")
    self.assertProduction([('a', Terminal), ('b', Terminal)], rules[0].nudProduction)
    self.assertProduction([('c', Terminal), ('d', NonTerminal)], rules[0].ledProduction)
    self.assertAstSpecification('NudAst', [], rules[0].nudAst)
    self.assertAstSpecification('Ast', [], rules[0].ast)

  def test_five(self):
    rules = self.parser.parse("expr := {'a' + 'b' -> NudAst()}")
    self.assertProduction([('a', Terminal), ('b', Terminal)], rules[0].nudProduction)
    self.assertProduction([], rules[0].ledProduction)
    self.assertAstSpecification('NudAst', [], rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

  def test_six(self):
    rules = self.parser.parse("expr := {'a'}")
    self.assertProduction([('a', Terminal)], rules[0].nudProduction)
    self.assertProduction([], rules[0].ledProduction)
    self.assertAstTranslation(0, rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

  def test_seven(self):
    rules = self.parser.parse("expr := {u}")
    self.assertProduction([('u', NonTerminal)], rules[0].nudProduction)
    self.assertProduction([], rules[0].ledProduction)
    self.assertAstTranslation(0, rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

  def test_eight(self):
    self.assertRaises(Exception, self.parser.parse, "expr := ")

  def test_nine(self):
    rules = self.parser.parse("expr := expr + 'plus' + expr")
    self.assertProduction([], rules[0].nudProduction)
    self.assertProduction([('plus', Terminal), ('expr', NonTerminal)], rules[0].ledProduction)
    self.assertAstTranslation(0, rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

  def test_ten(self):
    rules = self.parser.parse("expr := 'minus' + expr")
    self.assertProduction([('minus', Terminal), ('expr', NonTerminal)], rules[0].nudProduction)
    self.assertProduction([], rules[0].ledProduction)
    self.assertAstTranslation(0, rules[0].nudAst)
    self.assertAstTranslation(0, rules[0].ast)

if __name__ == '__main__':
  unittest.main()
