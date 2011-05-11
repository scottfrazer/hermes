import unittest, json
from GrammarTest import GrammarTest

class BaseGrammarTest(GrammarTest):

  def setUp(self):
    self.grammars = [ 
      {
        'json': {
              "ll1": {
                "start": "s",
                "rules": [
                  "s := t | u | _empty",
                  "t := 'a' | 'b'",
                  "u := list(v)",
                  "v := 'c'"
                ]
              }
            },
        'first': {
                  's': {'a', 'b', 'c', 'ε'},
                  't': {'a', 'b'},
                  'u': {'c'},
                  'v': {'c'}
                 },
        'follow': {
                    's': {'σ'},
                    't': {'σ'},
                    'u': {'σ'},
                    'v': {'σ', 'c'}
                  }
        }
    ]

  def test_firstSigmaAsciiEquivalent(self):
    self._test_firstFollow(0)
  
  def test_caseInsensitivityOfMorphemes(self):
    self.grammars[0]['json']['ll1']['start'] = 'S'
    self.grammars[0]['json']['ll1']['rules'][0] = 's := T | u | _empty'
    self.grammars[0]['json']['ll1']['rules'][1] = "t := 'A' | 'b'"
    self._test_firstFollow(0)

  def _test_firstFollow(self, idx):
    self.loadGrammarJson( self.grammars[idx]['json'] ) \
        .assertFirst( self.grammars[idx]['first'] ) \
        .assertFollow( self.grammars[idx]['follow'] )
if __name__ == '__main__':
  unittest.main()