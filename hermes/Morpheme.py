class Morpheme:
  def __init__(self, string, id=0):
    self.__dict__.update(locals())

class NonTerminal(Morpheme):
  def __init__(self, string, id=0, generated=False, macro=None):
    self.__dict__.update(locals())
    super().__init__(string, id)
  def id(self):
    return self.id
  def setMacro(self, macro):
    self.macro = macro
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__(self, theme=None):
    nt_str = '$' + self.string
    return theme.nonterminal(nt_str) if theme else nt_str
  def first(self):
    return 

class Terminal(Morpheme):
  def __init__(self, string, id=0):
    super().__init__(string, id)
    self.isSeparator = False
  def id(self):
    return self.id
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__(self, theme=None):
    t_str = ':' + self.string
    return theme.terminal(t_str) if theme else t_str
  def first(self):
    return {self}

class AbstractTerminal(Terminal):
  pass

class EmptyString(AbstractTerminal):
  def __init__(self, id):
    super().__init__('ε', id)
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__(self, theme=None):
    return theme.emptyString(':_empty') if theme else ':_empty'

class EndOfStream(AbstractTerminal):
  def __init__(self, id):
    super().__init__('σ', id)
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__(self, theme=None):
    return theme.endOfStream('σ') if theme else 'σ'
