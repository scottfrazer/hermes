from hermes.Morpheme import Morpheme

class Macro(Morpheme):
  id = -1

class ListMacro(Macro):
  def setFollow(self, follow):
    self.__dict__.update(locals())

# TODO: this class really isn't necessary
class LL1ListMacro(ListMacro):
  pass

# TODO: perhaps start_nt and rules should be a single 'Expansion' or 'Grammar' parameter
class MinimumListMacro(LL1ListMacro):
  def __init__( self, nonterminal, minimum, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<mlist (%s, %s)>' % (str(self.nonterminal), str(self.minimum))

class OptionalMacro(LL1ListMacro):
  def __init__( self, nonterminal, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<optional (%s)>' % (str(self.nonterminal))

class TerminatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, terminator, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<tlist (%s, %s)>' % (str(self.nonterminal), str(self.terminator))

class MorphemeListMacro(LL1ListMacro):
  def __init__( self, morpheme, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s)>' % (str(self.morpheme))

class SeparatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s, %s)>' % (str(self.nonterminal), str(self.separator))
