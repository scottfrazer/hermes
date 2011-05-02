import unittest
from hermes.GrammarFileParser import GrammarFileParser
from hermes.Grammar import Grammar
from hermes.Conflict import FirstFirstConflict
from hermes.Conflict import FirstFollowConflict
from GrammarTest import GrammarTest

class ConflictGrammarTest(GrammarTest):
  def setUp(self):
    self.loadGrammarFile('grammars/conflict.zgr', 'S')
  
  def test_firstSets(self):
    self.assertFirst({
      's': {'c'},
      'a': {'c', 'ε'}
    })

  def test_followSets(self):
    self.assertFollow({
      's': {'σ'},
      'a': {'c'}
    })

  def test_conflicts(self):
    self.assertEqual(1, len(self.grammar.conflicts), "Expecting one conflict")
    self.assertEqual(FirstFollowConflict, type(self.grammar.conflicts[0]))

if __name__ == '__main__':
  unittest.main()
