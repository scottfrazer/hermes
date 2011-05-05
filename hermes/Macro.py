from hermes.Morpheme import Morpheme

class Macro(Morpheme):
  id = -1

class ListMacro(Macro):
  pass

class LL1ListMacro(ListMacro):
  def addFinishTerminalSet(t):
    self.finishTerminals = self.finishTerminals.union(t)

class ExprListMacro(ListMacro):
  def __init__( self, nonterminal, separator ):
    self.nonterminal = nonterminal
    self.separator = separator
  def __repr__( self ):
    return '<EXPR LIST (' + str(self.nonterminal) + ', ' + str(self.separator) + ')>'
  def expand( self ):
    pass

class NonterminalListMacro(LL1ListMacro):
  def __init__( self, nonterminal, start_nt, rules ):
    self.nonterminal = nonterminal
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<LIST (' + str(self.nonterminal) + ')>'

class SeparatedListMacro(LL1ListMacro):
  def __init__( self, nonterminal, separator, start_nt, rules ):
    self.nonterminal = nonterminal
    self.separator = separator
    self.start_nt = start_nt
    self.rules = rules
    self.finishTerminals = {}
    self.start_nt.setMacro(self)
  def __repr__( self ):
    return '<LIST (' + str(self.nonterminal) + ', ' + str(self.separator) + ')>'