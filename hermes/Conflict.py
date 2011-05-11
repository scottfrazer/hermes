class Conflict:
  pass

class ExprConflict(Conflict):
  def __init__( self, terminal, rules ):
    self.terminal = terminal
    self.rules = rules
  def __str__( self ):
    string = " -- %s conflict -- \n" % (self.type)
    string += "Terminal %s requires two different %s() functions.  Cannot choose between these rules:\n\n"%(self.terminal, self.type)
    for rule in self.rules:
      string += "(Rule-%d) %s\n" % (rule.id, rule)
    return string

class NudConflict(ExprConflict):
  type = "NUD"

class LedConflict(ExprConflict):
  type = "LED"

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
    string += "(Rule-%d)  %s\n" %(self.rule1.id, self.rule1)
    string += "(Rule-%d)  %s\n\n" %(self.rule2.id, self.rule2)
    string += "first(Rule-%d) = {%s}\n" %(self.rule1.id, ', '.join([str(e) for e in self.firstRule1]))
    string += "first(Rule-%d) = {%s}\n" %(self.rule2.id, ', '.join([str(e) for e in self.firstRule2]))
    string += "first(Rule-%d) ∩ first(Rule-%d): {%s}\n" % (self.rule1.id, self.rule2.id, ', '.join([str(e) for e in self.firstRule1.intersection(self.firstRule2)]))

    return string

class FirstFollowConflict(Conflict):
  def __init__( self, N, firstN, followN ):
    self.N = N
    self.firstN = firstN
    self.followN = followN

  def __str__( self ):
    string = ' -- FIRST/FOLLOW conflict --\n'
    string += 'Nonterminal %s has a first and follow set that overlap.\n\n' % (self.N)
    string += "first(%s) = {%s}\n" % (self.N, ', '.join([str(e) for e in self.firstN]))
    string += "follow(%s) = {%s}\n\n" % (self.N, ', '.join([str(e) for e in self.followN]))
    string += 'first(%s) ∩ follow(%s) = {%s}\n' % (self.N, self.N, ', '.join([str(e) for e in self.firstN.intersection(self.followN)]))

    return string
