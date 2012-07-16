from collections import OrderedDict
import json

class Conflict:
  pass

class Warning:
  pass

class UnusedNonterminalWarning(Warning):
  def __init__(self, nonterminal):
    self.__dict__.update(locals())

  def toJson(self):
    return json.dumps(OrderedDict([
      ('type', '"UnusedNonterminalWarning"'),
      ('message', 'Nonterminal %s is defined but not used' % (self.nonterminal))
    ]))

  def __str__(self):
    string = ' -- Unused Nonterminal -- \n'
    string += 'Nonterminal %s is defined but not used' % (self.nonterminal)
    return string

class UndefinedNonterminalConflict(Conflict):
  def __init__(self, nonterminal):
    self.__dict__.update(locals())

  def toJson(self):
    return json.dumps(OrderedDict([
      ('type', '"UndefinedNonterminalConflict"'),
      ('message', 'Nonterminal %s is used but not defined' % (self.nonterminal))
    ]))

  def __str__(self):
    string = ' -- Undefined Nonterminal Conflict-- \n'
    string += 'Nonterminal %s is used but not defined' % (self.nonterminal)
    return string

class ExprConflict(Conflict):
  def __init__( self, terminal, rules ):
    self.terminal = terminal
    self.rules = rules
  def toJson(self):
    x = OrderedDict([
      ('type', 'ExprConflict'),
      ('message', 'Terminal %s requires two different %s() functions.' % (self.terminal, self.type))
    ])

    for index, rule in enumerate(sorted(self.rules, key=lambda x: str(x))):
      x['rule-{0}'.format(index)] = str(rule)
    return json.dumps(x, indent=2)
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

  def toJson(self):
    return json.dumps(OrderedDict([
      ('type', '"ListFirstFollowConflict"'),
      ('first(%s)'%(self.listMacro.nonterminal), sorted([e.string for e in self.firstNonterminal])),
      ('follow(%s)'%(self.listMacro), sorted([e.string for e in self.followList])),
      ('first(%s) ∩ follow(%s)'%(self.listMacro.nonterminal, self.listMacro), sorted([e.string for e in self.firstNonterminal.intersection(self.followList)]))
    ]), indent=2)

  def __str__( self ):
    string = " -- LIST FIRST/FOLLOW conflict --\n"
    string += "FIRST(%s) = {%s}\n" %(self.listMacro.nonterminal, ', '.join([str(e) for e in self.firstNonterminal]))
    string += "FOLLOW(%s) = {%s}\n" %(self.listMacro, ', '.join([str(e) for e in self.followList]))
    string += "FIRST(%s) ∩ FOLLOW(%s): {%s}\n" %(self.listMacro.nonterminal, self.listMacro, ', '.join([str(e) for e in self.firstNonterminal.intersection(self.followList)]))
    return string

class FirstFirstConflict(Conflict):
  def __init__( self, rule1, rule2, grammar ):
    self.__dict__.update(locals())

  def toJson(self):
    rule1_first = self.grammar.ruleFirst(self.rule1)
    rule2_first = self.grammar.ruleFirst(self.rule2)
    return json.dumps(OrderedDict([
      ('type', 'FirstFirstConflict'),
      ('rule-0',  str(self.rule1))
      ('rule-1',  str(self.rule2))
      ('first(rule-0)', [e.string for e in rule1_first])
      ('first(rule-1)', [e.string for e in rule2_first])
      ('first(rule-0) ∩ first(rule-1)', [x.string for x in sorted(list(rule1_first.intersection(rule2_first)))])
    ]), indent=2)

  def __str__( self ):
    rule1_first = self.grammar.ruleFirst(self.rule1)
    rule2_first = self.grammar.ruleFirst(self.rule2)
    string = " -- FIRST/FIRST conflict --\n"
    string += "Two rules for nonterminal %s have intersecting first sets.  Can't decide which rule to choose based on terminal.\n\n" %(self.rule1.nonterminal)
    string += "(Rule-%d)  %s\n" %(self.rule1.id, self.rule1)
    string += "(Rule-%d)  %s\n\n" %(self.rule2.id, self.rule2)
    string += "first(Rule-%d) = {%s}\n" %(self.rule1.id, ', '.join(sorted([str(e) for e in rule1_first])))
    string += "first(Rule-%d) = {%s}\n" %(self.rule2.id, ', '.join(sorted([str(e) for e in rule2_first])))
    string += "first(Rule-%d) ∩ first(Rule-%d): {%s}\n" % (self.rule1.id, self.rule2.id, ', '.join(sorted([str(e) for e in rule1_first.intersection(rule2_first)])))

    return string

class FirstFollowConflict(Conflict):
  def __init__( self, N, firstN, followN ):
    self.N = N
    self.firstN = firstN
    self.followN = followN

  def toJson(self):
    return json.dumps(OrderedDict([
      ('type', 'FirstFollowConflict'),
      ('first(%s)' % (self.N), sorted([e.string for e in self.firstN])),
      ('follow(%s)' % (self.N), sorted([e.string for e in self.followN])),
      ('first(%s) ∩ follow(%s)' % (self.N, self.N), sorted([z.string for z in self.firstN.intersection(self.followN)]))
    ]), indent=2)

  def __str__( self ):
    string = ' -- FIRST/FOLLOW conflict --\n'
    string += 'Nonterminal %s has a first and follow set that overlap.\n\n' % (self.N)
    string += "first(%s) = {%s}\n" % (self.N, ', '.join([str(e) for e in self.firstN]))
    string += "follow(%s) = {%s}\n\n" % (self.N, ', '.join([str(e) for e in self.followN]))
    string += 'first(%s) ∩ follow(%s) = {%s}\n' % (self.N, self.N, ', '.join([str(e) for e in self.firstN.intersection(self.followN)]))

    return string
