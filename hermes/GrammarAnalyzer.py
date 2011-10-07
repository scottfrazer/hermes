import sys
from hermes.Theme import Theme, TerminalDefaultTheme

class GrammarAnalyzer:
  def __init__(self, grammar):
    self.grammar = grammar

  def analyze( self, format='human', theme=None, file=sys.stdout ):
    if theme == None:
      theme = TerminalDefaultTheme()
    if not isinstance(theme, Theme):
      raise Exception('bad theme')

    file.write(theme.title('Terminals'))
    file.write(', '.join([ x.str(theme) for x in sorted(self.grammar.terminals, key=lambda x: x.string) ]) + "\n\n")
    file.write(theme.title('Non-Terminals'))
    file.write(', '.join([ x.str(theme) for x in sorted(self.grammar.nonterminals, key=lambda x: x.string) ]) + "\n\n")
    file.write(theme.title('Expanded LL(1) Rules'))
    file.write("\n".join([ rule.str(theme) for rule in sorted(self.grammar.getExpandedLL1Rules(), key=lambda x: x.nonterminal.string)]) + "\n\n")
    
    for exprGrammar in self.grammar.exprgrammars:
      rules = self.grammar.getExpandedExpressionRules(exprGrammar.nonterminal)
      file.write(theme.title('Expanded Expression Grammar (%s)' % (exprGrammar.nonterminal)))
      file.write("\n".join([ rule.str(theme) for rule in sorted(rules, key=lambda x: x.id)]) + "\n\n")

    file.write(theme.title('First sets'))
    for nonterminal in sorted(self.grammar.nonterminals, key=lambda x: x.string):
      file.write("%s: {%s}\n" % (theme.nonterminal(str(nonterminal)), ', '.join([theme.terminal(str(x)) for x in self.grammar.first[nonterminal]])))
    file.write('\n')

    file.write(theme.title('Follow sets'))
    for nonterminal in sorted(self.grammar.nonterminals, key=lambda x: x.string):
      file.write("%s: {%s}\n" % (theme.nonterminal(str(nonterminal)), ', '.join([theme.terminal(str(x)) for x in self.grammar.follow[nonterminal]])))
    file.write('\n')

    if ( len(self.grammar.warnings) ):
      file.write(theme.warning('Warnings'))
      for warning in self.grammar.warnings:
        file.write(str(warning) + '\n\n')

    if ( len(self.grammar.conflicts) ):
      file.write(theme.conflict('Conflicts'))
      for conflict in self.grammar.conflicts:
        file.write(str(conflict) + '\n\n')
      file.write(theme.conflictsFound('%d conflicts found\n' % len(self.grammar.conflicts)))
    else:
      file.write(theme.noConflicts("\nGrammar contains no conflicts!\n"))
  
