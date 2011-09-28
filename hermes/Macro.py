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
class TerminatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, terminator, start_nt=None, rules=None ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<tlist (%s, %s)>' % (str(self.nonterminal), str(self.terminator))

class NonterminalListMacro(LL1ListMacro):
  def __init__( self, nonterminal, start_nt=None, rules=None ):
    self.nonterminal = nonterminal
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s)>' % (str(self.nonterminal))

class SeparatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, start_nt=None, rules=None ):
    self.nonterminal = nonterminal
    self.separator = separator
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    if start_nt:
      self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s, %s)>' % (str(self.nonterminal), str(self.separator))
