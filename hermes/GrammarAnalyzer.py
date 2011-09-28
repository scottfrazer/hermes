import json, sys
from hermes.Morpheme import NonTerminal

class Stylizer:
  pass

class NullStylizer(Stylizer):
  pass

class AnsiStylizer(Stylizer):
  pass

class GrammarAnalyzer:
  def __init__(self, grammar):
    self.grammar = grammar
  def analyze( self, format='human', stylizer=None, file=sys.stdout ):
    if stylizer == None:
      stylizer = NullStylizer()
    if not isinstance(stylizer, Stylizer):
      raise Exception('bad stylizer')

    file.write(" -- Terminals --\n")
    file.write(', '.join([str(e) for e in sorted(self.grammar.terminals, key=lambda x: x.id)]) + "\n\n")
    file.write(" -- Non-Terminals --\n")
    file.write(', '.join([str(e) for e in sorted(self.grammar.nonterminals, key=lambda x: x.id)]) + "\n\n")
    file.write(" -- Normalized Grammar -- \n")
    file.write("\n".join([ str(r) for r in sorted(self.grammar.getRules(), key=lambda x: x.id)]) + "\n\n")
    
    for grammar in self.grammar.exprgrammars:
      file.write(" -- Expression Grammar (%s) -- \n" % (grammar.nonterminal))
      file.write("\n".join([ str(r) for r in sorted(grammar.rules, key=lambda x: x.id)]) + "\n\n")

    file.write(" -- First sets --\n")
    for N in sorted(self.grammar.first.keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      file.write("%s = {%s}\n" % (N, ', '.join([str(e) for e in self.grammar.first[N]])))
    file.write("\n -- Follow sets --\n")
    for N in sorted(self.grammar.follow.keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      file.write("%s = {%s}\n" % (N, ', '.join([str(e) for e in self.grammar.follow[N]])))
    if ( len(self.grammar.warnings) ):
      file.write("\n -- Warnings --\n")
      for warning in self.grammar.warnings:
        file.write('\n' + str(warning) + '\n')
    if ( len(self.grammar.conflicts) ):
      file.write("\n -- Grammar conflicts detected.  Grammar is not LL(1) --\n")
      for conflict in self.grammar.conflicts:
        file.write('\n' + str(conflict) + '\n')
    else:
      file.write("\nGrammar is LL(1)!\n")
  
