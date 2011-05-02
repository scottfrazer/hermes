class Conflict:
  pass

class ListFirstFollowConflict(Conflict):
  def __init__( self, listMacro, firstNonterminal, followList ):
    self.listMacro = listMacro
    self.firstNonterminal = firstNonterminal
    self.followList = followList

  def __str__( self ):
    string = " -- LIST FIRST/FOLLOW conflict --\n"
    string += "FIRST(%s) = {%s}\n" %(self.listMacro.nonterminal, ', '.join([str(e) for e in self.firstNonterminal]))
    string += "FOLLOW(%s) = {%s}\n" %(self.listMacro, ', '.join([str(e) for e in self.followList]))
    string += "FIRST(%s) ∩ FOLLOW(%s): {%s}\n" %(self.listMacro.nonterminal, self.listMacro, ', '.join([str(e) for e in self.firstNonterminal.intersection(self.followList)]))
    return string

class FirstFirstConflict(Conflict):
  def __init__( self, rule1, firstRule1, rule2, firstRule2 ):
    self.rule1 = rule1
    self.rule2 = rule2
    self.firstRule1 = firstRule1
    self.firstRule2 = firstRule2

  def __str__( self ):
    string = " -- FIRST/FIRST conflict --\n"
    string += "Two rules for nonterminal %s have intersecting first sets.  Can't decide which rule to choose based on terminal.\n\n" %(self.rule1.nonterminal)
    string += "(Rule-1)  %s\n" %(self.rule1)
    string += "(Rule-2)  %s\n\n" %(self.rule2)
    string += "first(Rule-1) = {%s}\n" %(', '.join([str(e) for e in self.firstRule1]))
    string += "first(Rule-2) = {%s}\n" %(', '.join([str(e) for e in self.firstRule2]))
    string += "first(Rule-1) ∩ first(Rule-2): {%s}\n" %(', '.join([str(e) for e in self.firstRule1.intersection(self.firstRule2)]))
    return string

class FirstFollowConflict(Conflict):
  def __init__( self, N, firstN, followN ):
    self.N = N
    self.firstN = firstN
    self.followN = followN

  def __str__( self ):
    string = ' -- FIRST/FOLLOW conflict --\n'
    string += 'NON-TERMINAL %s:  FIRST(%s) ∩ FOLLOW(%s) = {%s}\n' % (self.N, self.N, self.N, ', '.join([str(e) for e in self.firstN.intersection(self.followN)]))
    return string
