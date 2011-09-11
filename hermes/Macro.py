from hermes.Morpheme import Morpheme

class Macro(Morpheme):
  id = -1

class ListMacro(Macro):
  pass

class LL1ListMacro(ListMacro):
  pass

class ExprListMacro(ListMacro):
  def __init__( self, nonterminal, separator ):
    self.__dict__.update(locals())
  def setFollow( self, follow ):
    self.__dict__.update(locals())
  def __repr__( self ):
    return '<expr_list (' + str(self.nonterminal) + ', ' + str(self.separator) + ')>'
  def expand( self ):
    pass

class TerminatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, terminator, start_nt, rules ):
    self.__dict__.update(locals())
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<tlist (%s, %s)>' % (str(self.nonterminal), str(self.terminator))

class NonterminalListMacro(LL1ListMacro):
  def __init__( self, nonterminal, start_nt, rules ):
    self.nonterminal = nonterminal
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s)>' % (str(self.nonterminal))

class SeparatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, start_nt, rules ):
    self.nonterminal = nonterminal
    self.separator = separator
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<list (%s, %s)>' % (str(self.nonterminal), str(self.separator))
