import json
from hermes.Morpheme import NonTerminal

class GrammarAnalyzer:
  def __init__(self, grammar):
    self.grammar = grammar
  def analyze( self, format='human' ):
    print(" -- Terminals --")
    print(', '.join([str(e) for e in sorted(self.grammar.terminals, key=lambda x: x.id)]) + "\n")
    print(" -- Non-Terminals --")
    print(', '.join([str(e) for e in sorted(self.grammar.nonterminals, key=lambda x: x.id)]) + "\n")
    print(" -- Normalized Grammar -- ")
    print("\n".join([ str(r) for r in sorted(self.grammar.getNormalizedLL1Rules(), key=lambda x: x.id)]) + "\n")
    
    for grammar in self.grammar.exprgrammars:
      print(" -- Expression Grammar (%s) -- " % (grammar.nonterminal))
      print("\n".join([ str(r) for r in sorted(grammar.rules, key=lambda x: x.id)]) + "\n")

    print(" -- First sets --")
    for N in sorted(self.grammar.first().keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      print("%s = {%s}" % (N, ', '.join([str(e) for e in self.grammar.first(N)])))
    print("\n -- Follow sets --")
    for N in sorted(self.grammar.follow().keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      print("%s = {%s}" % (N, ', '.join([str(e) for e in self.grammar.follow(N)])))
    if ( len(self.grammar.conflicts) ):
      print("\n -- Grammar conflicts detected.  Grammar is not LL(1) --")
      for conflict in self.grammar.conflicts:
        print('\n' + str(conflict))
    else:
      print("\nGrammar is LL(1)!")
  