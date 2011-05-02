import json
from hermes.Morpheme import Terminal, EndOfStream, EmptyString

class GrammarAnalyzer:
  def __init__(self, grammar):
    self.grammar = grammar
  def analyze( self, format='human' ):
    print(" -- Terminals --")
    print(', '.join(["'" + str(e) + "'" for e in self.grammar.terminals]) + "\n")
    print(" -- Non-Terminals --")
    print(', '.join([str(e) for e in self.grammar.nonterminals]) + "\n")
    print(" -- Normalized Grammar -- ")
    print(self.grammar.__str__(True))
    print("\n -- First sets --")
    for N, t in self.grammar.first.items():
      if type(N) is Terminal or type(N) is EmptyString or type(N) is EndOfStream:
        continue
      print("%s = {%s}" % (N, ', '.join([str(e) for e in t])))
    print("\n -- Follow sets --")
    for N, t in self.grammar.follow.items():
      print("%s = {%s}" % (N, ', '.join([str(e) for e in t])))
    if ( len(self.grammar.conflicts) ):
      print("\n -- Grammar conflicts detected.  Grammar is not LL(1) --")
      for conflict in self.grammar.conflicts:
        print('\n' + str(conflict))
    else:
      print("\nGrammar is LL(1)!")
  