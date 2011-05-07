import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from hermes.Conflict import FirstFirstConflict, FirstFollowConflict, NudConflict
from GrammarTest import GrammarTest

class ConflictGrammarTest(GrammarTest):
  def test_firstSets(self):
    self.loadGrammarFile('grammars/conflict.zgr', 'S') \
        .assertFirst({
          's': {'c'},
          'a': {'c', 'ε'}
        })

  def test_followSets(self):
    self.loadGrammarFile('grammars/conflict.zgr', 'S') \
        .assertFollow({
          's': {'σ'},
          'a': {'c'}
        })

  def test_conflicts(self):
    self.loadGrammarFile('grammars/conflict.zgr', 'S')
    self.assertEqual(1, len(self.grammar.conflicts), "Expecting one conflict")
    self.assertEqual(FirstFollowConflict, type(self.grammar.conflicts[0]))
  
  def test_conflicts(self):
    self.loadGrammarFile('grammars/expr1.zgr')
    self.assertEqual(1, len(self.grammar.conflicts), "Expecting one conflict")
    self.assertEqual(NudConflict, type(self.grammar.conflicts[0]))
  
  
if __name__ == '__main__':
  unittest.main()
