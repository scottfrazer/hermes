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
  def __init__( self, nonterminal, minimum, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'mlist({0}, {1})'.format(str(self.nonterminal), str(self.minimum))

class OptionalMacro(LL1ListMacro):
  def __init__( self, nonterminal, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'optional({0})'.format(str(self.nonterminal))

class TerminatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, terminator, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'tlist({0}, {1})'.format(str(self.nonterminal), str(self.terminator))

class MorphemeListMacro(LL1ListMacro):
  def __init__( self, morpheme, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'list({0})'.format(str(self.morpheme))

class SeparatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'list({0}, {1})'.format(str(self.nonterminal), str(self.separator))

class OptionallyTerminatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, minimum, start_nt, rules ):
    self.__dict__.update(locals())
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return 'otlist({0}, {1}, {2})'.format(str(self.nonterminal), str(self.separator), self.minimum)
