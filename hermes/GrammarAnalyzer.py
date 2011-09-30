import sys
from hermes.Morpheme import NonTerminal

class Stylizer:
  pass

class NullStylizer(Stylizer):
  def color(self, string, color = None):
    return string 

class AnsiStylizer(Stylizer):
  def __init__(self):
    self.colors = {
        'purple': '\033[95m',
        'blue': '\033[94m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
    }
    self.endc = '\033[0m'

  def color(self, string, color = None):
    if color in self.colors:
      return "%s%s%s" % (self.colors[color], string, self.endc)
    return string

class GrammarAnalyzer:
  def __init__(self, grammar):
    self.grammar = grammar

  def _title(self, string, stylizer):
    return self._boxed(string, stylizer, 'blue')

  def _warning(self, string, stylizer):
    return self._boxed(string, stylizer, 'yellow')

  def _conflict(self, string, stylizer):
    return self._boxed(string, stylizer, 'red')

  def _boxed(self, string, stylizer, color):
    line = '+%s+' % (''.join(['-' for i in range(len(string)+2)]))
    return stylizer.color('%s\n| %s |\n%s\n\n' % (line, string, line), color)

  def analyze( self, format='human', stylizer=None, file=sys.stdout ):
    if stylizer == None:
      stylizer = AnsiStylizer()
    if not isinstance(stylizer, Stylizer):
      raise Exception('bad stylizer')

    file.write(self._title('Terminals', stylizer))
    file.write(', '.join([str(e) for e in sorted(self.grammar.terminals, key=lambda x: x.id)]) + "\n\n")
    file.write(self._title('Non-Terminals', stylizer))
    file.write(', '.join([str(e) for e in sorted(self.grammar.nonterminals, key=lambda x: x.id)]) + "\n\n")
    file.write(self._title('Expanded LL(1) Rules', stylizer))
    file.write("\n".join([ str(r) for r in sorted(self.grammar.getExpandedLL1Rules(), key=lambda x: str(x))]) + "\n\n")
    
    for exprGrammar in self.grammar.exprgrammars:
      rules = self.grammar.getExpandedExpressionRules(exprGrammar.nonterminal)
      file.write(self._title('Expanded Expression Grammar (%s)' % (exprGrammar.nonterminal), stylizer))
      file.write("\n".join([ str(r) for r in sorted(rules, key=lambda x: x.id)]) + "\n\n")

    file.write(self._title('First sets', stylizer))
    for N in sorted(self.grammar.first.keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      file.write("%s = {%s}\n" % (N, ', '.join([str(e) for e in self.grammar.first[N]])))
    file.write('\n')

    file.write(self._title('Follow sets', stylizer))
    for N in sorted(self.grammar.follow.keys(), key=lambda x: x.id):
      if not isinstance(N, NonTerminal):
        continue
      file.write("%s = {%s}\n" % (N, ', '.join([str(e) for e in self.grammar.follow[N]])))
    file.write('\n')

    if ( len(self.grammar.warnings) ):
      file.write(self._warning('Warnings', stylizer))
      for warning in self.grammar.warnings:
        file.write(str(warning) + '\n\n')

    if ( len(self.grammar.conflicts) ):
      file.write(self._conflict('Conflicts', stylizer))
      for conflict in self.grammar.conflicts:
        file.write(str(conflict) + '\n\n')
      file.write(stylizer.color('%d conflicts found\n' % len(self.grammar.conflicts), 'red'))
    else:
      file.write(stylizer.color("\nGrammar contains no conflicts!\n", 'green'))
  
