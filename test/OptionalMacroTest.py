import unittest
from GrammarTest import GrammarTest

class OptionalMacroTest(GrammarTest):

  def test_optional1GrammarFile_1(self):
    self.loadGrammarFile('grammars/optional1.zgr', 's')
    self.runWithTokens(['x'])
    self.assertParseTree('(s: (_gen0: (t: x)))')
    self.assertAst('x')
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

  def test_optional1GrammarFile_2(self):
    self.loadGrammarFile('grammars/optional1.zgr', 's')
    self.runWithTokens([])
    self.assertParseTree('(s: )')
    self.assertAst('none')
    self.assertEqual(0, len(self.grammar.conflicts), "Expected zero conflicts")

if __name__ == '__main__':
  unittest.main()
