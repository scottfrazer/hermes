class Morpheme:
  pass

class NonTerminal(Morpheme):
  def __init__(self, string, id=0):
    self.string = string
    self.id = id
    self.macro = None # Is this nonterminal the root of a macro expansion?
  def id(self):
    return self.id
  def setMacro(self, macro):
    self.macro = macro
  def __str__(self):
    return self.string
  def first(self):
    return 

class Terminal(Morpheme):
  def __init__(self, string, id=0):
    self.string = string
    self.id = id
  def id(self):
    return self.id
  def __str__(self):
    return "'" + self.string + "'"
  def first(self):
    return {self}

class AbstractTerminal(Terminal):
  pass

class EmptyString(AbstractTerminal):
  def __init__(self, id):
    super(EmptyString, self).__init__('ε', id)
  def __str__(self):
    return 'ε'

class EndOfStream(AbstractTerminal):
  def __init__(self, id):
    super(EndOfStream, self).__init__('σ', id)
  def __str__(self):
    return 'σ'

class Expression(AbstractTerminal):
  def __init__(self, id):
    super(Expression, self).__init__('λ', id)
  def __str__(self):
    return 'λ'
