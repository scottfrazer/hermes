from xtermcolor.ColorMap import XTermColorMap

class AnsiStylizer:
  def __init__(self):
    self.colormap = XTermColorMap()
  def color(self, string, ansi):
    return self.colormap.colorize(string, ansi=ansi)

class Theme:
  def rule(self, string):
    return string
  def production(theme, string):
    return string
  def nonterminal(theme, string):
    return string
  def terminal(self, string):
    return string
  def endOfStream(self, string):
    return string
  def emptyString(self, string):
    return string
  def expression(self, string):
    return string
  def expressionRule(self, string):
    return string
  def infixOperator(self, string):
    return string
  def prefixOperator(self, string):
    return string
  def mixfixOperator(self, string):
    return string
  def title(self, string):
    return string
  def warning(self, string):
    return string
  def conflict(self, string):
    return string
  def conflictsFound(self, string):
    return string
  def noConflicts(self, string):
    return string
  def astTranslation(self, string):
    return string
  def astSpecification(self, string):
    return string

class TerminalDefaultTheme(Theme):
  def title(self, string):
    return string + '\n'
  def warning(self, string):
    return string + '\n'
  def conflict(self, string):
    return string + '\n'

class TerminalColorTheme(Theme):
  def __init__(self, ansiStylizer):
    self.__dict__.update(locals())
  def rule(self, string):
    return string
  def production(self, string):
    return string
  def nonterminal(self, string):
    return self.ansiStylizer.color(string, 2)
  def terminal(self, string):
    return "'" + self.ansiStylizer.color(string.strip("'"), 14) + "'"
  def endOfStream(self, string):
    return string
  def emptyString(self, string):
    return string
  def expression(self, string):
    return string
  def expressionRule(self, string):
    return string
  def infixOperator(self, string):
    return string
  def prefixOperator(self, string):
    return string
  def mixfixOperator(self, string):
    return string
  def title(self, string):
    return self._boxed(string, 4)
  def warning(self, string):
    return self._boxed(string, 11)
  def conflict(self, string):
    return self._boxed(string, 2)
  def conflictsFound(self, string):
    return self.ansiStylizer.color(string, 2)
  def noConflicts(self, string):
    return self.ansiStylizer.color(string, 2)
  def astTranslation(self, string):
    return string
  def astSpecification(self, string):
    return self.ansiStylizer.color(string, 13)
  def _boxed(self, string, color):
    line = '+%s+' % (''.join(['-' for i in range(len(string)+2)]))
    return self.ansiStylizer.color('%s\n| %s |\n%s\n\n' % (line, string, line), color)
