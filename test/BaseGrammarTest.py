import unittest, json
from GrammarTest import GrammarTest

class BaseGrammarTest(GrammarTest):

  def test_firstSigmaAsciiEquivalent(self):
    grammar = {
      "ll1": {
        "start": "s",
        "rules": [
          "s := _empty"
        ]
      }
    }
    self.loadGrammarStr(json.dumps(grammar)) \
        .assertFirst({
          's': {'ε'}
         })

if __name__ == '__main__':
  unittest.main()
