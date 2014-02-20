from copy import copy
from collections import OrderedDict
from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Morpheme, AbstractTerminal
from hermes.Conflict import FirstFirstConflict, FirstFollowConflict, ListFirstFollowConflict, NudConflict, LedConflict, UndefinedNonterminalConflict, UnusedNonterminalWarning
from hermes.Macro import ListMacro, LL1ListMacro, SeparatedListMacro, MorphemeListMacro
from hermes.Logger import Factory as LoggerFactory

moduleLogger = LoggerFactory().getModuleLogger(__name__)

class Production:
  def __init__( self, morphemes = [] ):
    self.__dict__.update(locals())
  def __len__( self ):
    return len(self.morphemes)
  def str( self, theme=None ):
    return self.__str__(theme)
  def __str__( self, theme=None ):
    return ' '.join([ (p.str(theme) if theme else str(p)) for p in self.morphemes ])

class Rule:
  def __init__( self, nonterminal, production, id=None, root=None, ast=None):
    self.__dict__.update(locals())
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  def __copy__( self ):
    return Rule(self.nonterminal, Production(copy(self.production.morphemes)), self.id, self.root, self.ast)
  def isTokenAlias(self):
    if len(self.production.morphemes) == 1 and isinstance(self.production.morphemes[0], Terminal):
      return self.production.morphemes[0]
    return False
  def isAliasFor(self, terminal_str):
    # terminal alias rule is a rule in the form nt := 'terminal'
    return len(self.production.morphemes) == 1 and isinstance(self.production.morphemes[0], Terminal) and self.production.morphemes[0].string == terminal_str
  def expand( self ):
    morphemes = []
    rules = []
    for m in self.production.morphemes:
      if isinstance(m, LL1ListMacro):
        rules.extend(m.rules)
        morphemes.append(m.start_nt)
      else:
        morphemes.append(m)
    rules.append(Rule(self.nonterminal, Production(morphemes), self.id, self.root, self.ast))
    self.logger.debug('[rule expansion] %s becomes %s' % (self, ', '.join([str(x) for x in rules])))
    return rules

  def str( self, theme = None ):
    return self.__str__( theme )

  def __str__( self, theme = None ):
    ast = ''
    if self.ast and not (isinstance(self.ast, AstTranslation) and self.ast.idx == 0):
      ast = ' -> {0}'.format(self.ast.str(theme) if theme else self.ast)

    nonterminal = self.nonterminal.str(theme) if theme else str(self.nonterminal)
    production = self.production.str(theme) if theme else str(self.production)
    rule = "{0} = {1}{2}".format( nonterminal, production, ast)
    return theme.rule(rule) if theme else rule

  def __eq__(self, other):
    if str(other) == str(self):
      return True
    return False

  def __hash__(self):
    return hash(str(self))

  def getProduction(self):
    return self.production

  def getNonTerminal(self):
    return self.nonterminal

class MacroGeneratedRule(Rule):
  pass

class RuleExpander():
  def __init__( self, rules ):
    self.rules = rules
  def expand( self ):
    return self._flatten([e.expand() for e in self.rules])
  def _flatten( self, l ):
    f = []
    for i in l:
      if isinstance(i, list):
        f.extend(i)
      else:
        f.append(i)
    return f

class Ast:
  pass

class AstSpecification:
  def __init__( self, name, parameters ):
    self.name = name
    self.parameters = parameters
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__( self, theme=None ):
    string = self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )' 
    return theme.astSpecification(string) if theme else string

class AstTranslation:
  def __init__( self, idx ):
    self.idx = idx
  def str(self, theme=None):
    return self.__str__(theme)
  def __str__( self, theme=None ):
    string = '$' + str(self.idx)
    return theme.astTranslation(string) if theme else string

class ExprRule:
  def __init__(self, nonterminal, nudProduction, ledProduction, nudAst, ast, operator):
    self.__dict__.update(locals())
    if (not nudProduction or not len(nudProduction)) and \
       (not ledProduction or not len(ledProduction)):
      raise Exception('Rule must contain a NUD or a LED portion.')
    if self.getRoot() and not isinstance(self.getRoot(), Terminal):
      raise Exception('Root of expression rule must be a terminal.')
  def __copy__( self ):
    np = Production(copy(self.nudProduction.morphemes))
    lp = Production(copy(self.ledProduction.morphemes))
    return ExprRule(self.nonterminal, np, lp, self.nudAst, self.ast, self.operator)
  def isTokenAlias(self):
    if len(self.nudProduction) == 1 and isinstance(self.nudProduction.morphemes[0], Terminal):
      return self.nudProduction.morphemes[0]
    return False
  def isAliasFor(self, terminal_str):
    # terminal alias rule is a rule in the form nt := 'terminal'
    return len(self.nudProduction) == 1 and isinstance(self.nudProduction.morphemes[0], Terminal) and self.nudProduction.morphemes[0].string == terminal_str
  def getRoot(self):
    if self.ledProduction and len(self.ledProduction):
      return self.ledProduction.morphemes[0]
    return None
  def expand(self):
    nudMorphemes = []
    ledMorphemes = []
    rules = []
    for morpheme in self.nudProduction.morphemes:
      if isinstance(morpheme, LL1ListMacro):
        rules.extend(morpheme.rules)
        nudMorphemes.append(morpheme.start_nt)
      else:
        nudMorphemes.append(morpheme)
    for morpheme in self.ledProduction.morphemes:
      if isinstance(morpheme, LL1ListMacro):
        rules.extend(morpheme.rules)
        ledMorphemes.append(morpheme.start_nt)
      else:
        ledMorphemes.append(morpheme)
    rules.append(ExprRule(self.nonterminal, Production(nudMorphemes), Production(ledMorphemes), self.nudAst, self.ast, self.operator))
    return rules
  def getProduction(self):
    return self.nudProduction
  def getNonTerminal(self):
    return self.nonterminal
  def str(self, theme = None):
    return self.__str__(theme)
  def __str__(self, theme = None):
    def ast_to_str(ast):
      if isinstance(ast, AstTranslation) and ast.idx == 0:
        return ''
      return ' -> ' + ast.str(theme) if ast else ''

    if isinstance(self.operator, InfixOperator):
      string = '{nt} = {nt} {op} {nt}{ast}'.format(nt=self.nonterminal, op=self.operator.operator, ast=ast_to_str(self.ast))
    elif isinstance(self.operator, PrefixOperator):
      string = '{nt} = {op} {nt}{ast}'.format(nt=self.nonterminal, op=self.operator.operator, ast=ast_to_str(self.ast))
    elif isinstance(self.operator, MixfixOperator):
      led = ' <=> {}'.format(self.ledProduction.str(theme)) if len(self.ledProduction.morphemes) else ''
      string = '{nt} = {nud}{nud_ast}{led}{ast}'.format(
          nt=self.nonterminal, nud=self.nudProduction.str(theme), nud_ast=ast_to_str(self.nudAst), led=led, ast=ast_to_str(self.ast)
      )
    else:
      string = '{nt} = {nud}{ast}'.format(nt=self.nonterminal, nud=self.nudProduction.str(theme), ast=ast_to_str(self.ast))

    return theme.expressionRule(string) if theme else string

class Operator:
  def __init__(self, operator, binding_power, associativity):
    self.__dict__.update(locals())
  def str(self, theme=None):
    return '<Operator {}, binding_power={}, associativity={}>'.format(self.operator, self.binding_power, self.associativity)
  def __str__(self):
    return self.str()

class InfixOperator(Operator):
  def str(self, theme=None):
    return "<Infix {}>".format(super(InfixOperator, self).str(theme))

class PrefixOperator(Operator):
  def str(self, theme=None):
    return "<Prefix {}>".format(super(PrefixOperator, self).str(theme))

class MixfixOperator(Operator):
  def str(self, theme=None):
    return "<Mixfix {}>".format(super(MixfixOperator, self).str(theme))

class OperatorPrecedence:
  def __init__(self, terminal, precedence, associativity):
    self.__dict__.update(locals())
  def str(self, theme = None):
    return self.__str__(theme)
  def __str__(self, theme = None):
    return 'OperatorPrecedence(%s, %s, %s)' % (str(self.terminal), self.precedence, self.associativity)

class FirstFollowCalculator:
  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  # This is duplicated
  def _pfirst( self, grammar, P ):
    r = set()
    addEpsilon = True
    for m in P.morphemes:
      if isinstance(m, MorphemeListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      toks = self.first[m].difference({grammar._empty})
      if len(toks) > 0:
        r = r.union(toks)
      if grammar._empty not in self.first[m]:
        addEpsilon = False
        break
    if addEpsilon:
      r = r.union({grammar._empty})
    return r

  def update(self, grammar, first, follow):
    change = False
    for nonterminal, terminals in first.items():
      if nonterminal not in self.first:
        self.first[nonterminal] = first[nonterminal]
        continue

      if not self.first[nonterminal].issuperset(first[nonterminal]):
        change = True
        self.first[nonterminal] = self.first[nonterminal].union(first[nonterminal])

    for nonterminal, terminals in follow.items():
      if nonterminal not in self.follow:
        self.follow[nonterminal] = follow[nonterminal]
        continue

      if not self.follow[nonterminal].issuperset(follow[nonterminal]):
        change = True
        self.follow[nonterminal] = self.follow[nonterminal].union(follow[nonterminal])

    self._computeFirst(grammar)
    self._computeFollow(grammar)
    return (self.first, self.follow, change)

class LL1FirstFollowCalculator(FirstFollowCalculator):
  def compute(self, grammar):
    if not isinstance(grammar, LL1Grammar):
      raise Exception('Grammar must be an LL1 grammar')

    self._init(grammar)
    self._computeFirst(grammar)
    self._computeFollow(grammar)
    return (self.first, self.follow)

  def _init(self, grammar):
    self.first = {x: set() for x in grammar.nonterminals}
    self.follow = {x: set() for x in grammar.nonterminals}
    self.first.update({x: {x} for x in grammar.terminals})
    self.follow.update({x: set() for x in grammar.macros})
    self.first.update({x: set() for x in grammar.macros if isinstance(x, LL1ListMacro)})
    for rule in grammar.expandedRules:
      if len(rule.production.morphemes) == 1 and grammar._empty in rule.production.morphemes:
        self.first[rule.nonterminal].union({grammar._empty})
    if grammar.start:
      self.follow[ grammar.start ] = {grammar._end}

  def _computeFirst(self, grammar):
    changed = False
    progress = True
    while progress == True:
      progress = False
      for rule in grammar.expandedRules:
        try:
          morpheme = rule.production.morphemes[0]
        except IndexError:
          continue

        # TODO: filter out extraneous _empty's in grammar files (e.g. x := _empty + 'a' + _empty)
        if (isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString)) and \
           morpheme not in self.first[rule.nonterminal]:
          progress = changed = True
          self.logger.debug('first(%s) = {%s} ∪ {%s}' % (rule.nonterminal, ', '.join([str(x) for x in self.first[rule.nonterminal]]), morpheme))
          self.first[rule.nonterminal] = self.first[rule.nonterminal].union({morpheme})

        elif isinstance(morpheme, NonTerminal) or isinstance(morpheme, LL1ListMacro):
          addEpsilon = True
          for morpheme in rule.production.morphemes:
            if isinstance(morpheme, LL1ListMacro):
              sub = self.first[morpheme.start_nt]
            else:
              sub = self.first[morpheme]
            if not self.first[rule.nonterminal].issuperset(sub.difference({grammar._empty})):
              progress = changed = True
              self.logger.debug('first(%s) = {%s} ∪ {%s}' % ( \
                        rule.nonterminal, \
                        ', '.join([str(x) for x in self.first[rule.nonterminal]]), \
                        ', '.join([str(x) for x in sub.difference({grammar._empty})]) \
                      ))
              self.first[rule.nonterminal] = self.first[rule.nonterminal].union(sub.difference({grammar._empty}))
            if grammar._empty not in sub:
              addEpsilon = False
              break
          if addEpsilon:
            self.first[rule.nonterminal] = self.first[rule.nonterminal].union({grammar._empty})
    return changed
  
  def _computeFollow( self, grammar ):
    changed = False

    progress = True
    while progress == True:
      progress = False

      for rule in grammar.expandedRules:
        for index, morpheme in enumerate(rule.production.morphemes):

          if isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString):
            continue

          try:
            nextToken = rule.production.morphemes[ index + 1 ]
          except IndexError:
            nextToken = None

          if nextToken:
            newTokens = self.first[nextToken].difference({grammar._empty})
            if not self.follow[morpheme].issuperset(newTokens):
              progress = changed = True
              self.logger.debug('follow(%s) = {%s} ∪ {%s}' % ( \
                morpheme, \
                ', '.join([str(x) for x in self.follow[morpheme]]), \
                ', '.join([str(x) for x in newTokens]) \
              ))
              self.follow[morpheme] = self.follow[morpheme].union(newTokens)

          if not nextToken or grammar._empty in self._pfirst(grammar, Production(rule.production.morphemes[index+1:])):
            z = self.follow[rule.nonterminal]
            y = self.follow[morpheme]

            if not y.issuperset(z):
              progress = changed = True
              self.logger.debug('follow(%s) = {%s} ∪ {%s}' % ( \
                morpheme, \
                ', '.join([str(x) for x in y]), \
                ', '.join([str(x) for x in z]) \
              ))
              self.follow[morpheme] = y.union(z)
    return changed

class ExpressionFirstFollowCalculator(FirstFollowCalculator):
  def compute(self, grammar):
    if not isinstance(grammar, ExpressionGrammar):
      raise Exception('Grammar must be an expression grammar')
    self._init(grammar)
    self._computeFirst(grammar)
    self._computeFollow(grammar)
    return ( self.first, self.follow )

  def _init(self, grammar):
    self.first = {x: set() for x in grammar.nonterminals}
    self.follow = {x: set() for x in grammar.nonterminals}
    self.first.update({x: {x} for x in grammar.terminals})
    self.follow.update({x: set() for x in grammar.macros})
    self.first.update({x: set() for x in grammar.macros if isinstance(x, LL1ListMacro)})

  def _computeFirst(self, grammar):
    for rule in grammar.rules:
      if len(rule.nudProduction):
        firstSet = self._pfirst(grammar, rule.nudProduction).difference({grammar._empty})
        self.first[rule.nonterminal] = self.first[rule.nonterminal].union(firstSet)

  def _computeFollow(self, grammar):
    for rule in grammar.rules:
      morphemes = []
      if rule.nudProduction.morphemes:
        morphemes.extend(rule.nudProduction.morphemes)
      if rule.ledProduction.morphemes:
        morphemes.extend(rule.ledProduction.morphemes)
      for index, morpheme in enumerate(morphemes):
        try:
          if isinstance(morphemes[index + 1], NonTerminal):
            theSet = self.follow[morphemes[index + 1]]
          elif isinstance(morphemes[index + 1], Terminal):
            theSet = {morphemes[index + 1]}

          if morpheme == rule.nonterminal:
            self.follow[rule.nonterminal] = self.follow[rule.nonterminal].union(theSet)
          elif isinstance(morpheme, ListMacro):
            morpheme.setFollow(theSet)

        except IndexError:
          continue

class Regex:
  def __init__(self, regex, options, terminal, function=None):
    self.__dict__.update(locals())

class Lexer(dict):
  code = ''
  def str(self, theme=None):
    return ', '.join(self.keys())

class Grammar:
  _empty = EmptyString(-1)
  _end = EndOfStream(-1)
  rules = []
  start = None
  tLookup = None
  ntLookup = None

  def __init__(self, name, rules):
    self.__dict__.update(locals())
    self.expandedRules = []
    self.conflicts = []
    self.nonterminals = []
    self.terminals = []
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)

    # Store in a str(rule) -> rule map to eliminate duplicate rules
    expanded_rules = OrderedDict()
    for rule in rules.copy():
      for expanded_rule in rule.expand():
        expanded_rules[str(expanded_rule)] = expanded_rule
    self.expandedRules = list(expanded_rules.values())

  def updateFirstFollow( self, first, follow ):
      (self.first, self.follow, changed) = self.firstFollowCalc.update(self, first, follow)
      return changed
  
  def _assignIds(self):
    i = 0
    for terminal in self.terminals:
      if self.isSimpleTerminal(terminal):
        terminal.id = i
        i += 1
    for nonterminal in self.nonterminals:
      nonterminal.id = i
      i += 1

    for ruleSet in [self.rules, self.expandedRules]:
      for i, rule in enumerate(ruleSet):
        rule.id = i

  def isSimpleTerminal( self, t ):
    return isinstance(t, Terminal) and not isinstance(t, AbstractTerminal)
  
  def isSpecialTerminal( self, t ):
    return isinstance(t, AbstractTerminal)
  
  def isTerminal( self, t ):
    return isinstance(t, Terminal)
  
  def isNonTerminal( self, n ):
    return isinstance(n, NonTerminal)
  
  def getTerminal( self, string ):
    if not self.tLookup:
      self.tLookup = dict()
      for terminal in self.terminals:
        self.tLookup[terminal.string.lower()] = terminal
    return self.tLookup[string]
  
  def getNonTerminal( self, string ):
    if not self.ntLookup:
      self.ntLookup = dict()
      for nonterminal in self.nonterminals:
        self.ntLookup[nonterminal.string.lower()] = nonterminal
    return self.ntLookup[string]
 
  def ruleFirst(self, rule):
    return self._pfirst(rule.production)

  # These should be pre-calculated.  also this is duplicated
  def _pfirst( self, P ):
    r = set()
    addEpsilon = True
    for m in P.morphemes:
      if isinstance(m, MorphemeListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      toks = self.first[m].difference({self._empty})
      if len(toks) > 0:
        r = r.union(toks)
      if self._empty not in self.first[m]:
        addEpsilon = False
        break
    if addEpsilon:
      r = r.union({self._empty})
    return r
  
  def getExpandedRules( self, nonterminal = None ):
    if nonterminal:
      return [rule for rule in self.expandedRules if str(rule.nonterminal) == str(nonterminal)]
    return self.expandedRules
  
  def getRules( self, nonterminal = None ):
    if nonterminal:
      return [rule for rule in self.rules if str(rule.nonterminal) == str(nonterminal)]
    return self.rules
  

class NudLedContainer:
  def __init__(self, morphemes, rule, bindingPower = None):
    self.__dict__.update(locals())
  def __len__(self):
    return len(self.morphemes)
  def __str__(self):
    pass

class ExpressionGrammar(Grammar):
  def __init__(self, nonterminals, terminals, macros, rules, precedence, nonterminal, firstFollowCalc):
    if not isinstance(rules, list):
      raise Exception("Expression grammar expecting an ordered list of rules to express operator precedence.")
    super().__init__('expr', rules) # TODO: fix this first parameter
    self.__dict__.update(locals())
    self._assignIds()
    if isinstance(precedence, dict):
      self.computedPrecedence = precedence
    else:
      self._computePrecedence()
    (self.first, self.follow) = firstFollowCalc.compute(self)
    self._computeConflicts()

  def extend(self, exprGrammar):
    self.rules = self.rules.union({copy(rule) for rule in exprGrammar.rules})
    self.expandedRules = self.expandedRules.union({copy(rule) for rule in exprGrammar.expandedRules})
    for ruleSet in [self.rules, self.expandedRules]:
      for rule in ruleSet:
        rule.nonterminal = self.nonterminal
        if not isinstance(rule, ExprRule):
          continue
        for index, atom in enumerate(rule.nudProduction.morphemes):
          if atom == exprGrammar.nonterminal:
            rule.nudProduction.morphemes[index] = self.nonterminal
        for index, atom in enumerate(rule.ledProduction.morphemes):
          if atom == exprGrammar.nonterminal:
            rule.ledProduction.morphemes[index] = self.nonterminal
    self.nonterminals = self.nonterminals.union(exprGrammar.nonterminals)
    self.terminals = self.terminals.union(exprGrammar.terminals)
    self.macros = self.macros.union(exprGrammar.macros)
    self.precedence = exprGrammar.precedence + self.precedence
    self._computePrecedence()
    (self.first, self.follow) = self.firstFollowCalc.compute(self)
    self._computeConflicts()

  def getExpandedExpressionRules(self, nonterminal = None):
    allRules = [rule for rule in self.expandedRules if isinstance(rule, ExprRule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

  # TODO: Get rid of this
  def _computePrecedence(self):
    counter = 1000
    self.computedPrecedence = {}
    for precedence in self.precedence:
      for terminal in precedence['terminals']:
        if terminal not in self.computedPrecedence:
          self.computedPrecedence[terminal] = list()
        self.computedPrecedence[terminal].append( OperatorPrecedence(terminal, counter, precedence['associativity']) )
      counter += 1000
  
  def getPrecedence(self):
    return self.computedPrecedence
 
  def ruleFirst(self, rule):
    if len(rule.nudProduction) and rule.nudProduction.morphemes[0] != rule.nonterminal:
      return self._pfirst(rule.nudProduction)
    return set()
  
  def _computeConflicts( self ):
    nud = {}
    led = {}
    self.conflicts = []

    morphemes = set(self.terminals).union(set(self.nonterminals))
    for m in morphemes:
      nud[m] = []
      led[m] = []

    for rule in self.expandedRules:
      try:
        if len(rule.nudProduction):
          morphemes = rule.nudProduction.morphemes
          nud[morphemes[0]].append( NudLedContainer(morphemes, rule) )
      except AttributeError:
        pass

      try:
        if len(rule.ledProduction):
          morphemes = rule.ledProduction.morphemes
          led[morphemes[0]].append( NudLedContainer(morphemes, rule) )
      except AttributeError:
        pass

    # if two rules parse the exact same atoms, they're the same rule
    def dedupe_func(x, y):
      for index in range(max(len(y), len(x))):
        try:
          if x.morphemes[index] != y.morphemes[index]:
            return False
        except IndexError:
          return False
      return True

    # Filter out unused items
    nud = {k: v for k, v in nud.items() if len(v)}
    led = {k: v for k, v in led.items() if len(v)}

    self.nud = {}
    self.led = {}

    # dedupe the list of rules for each terminal, should only be 1 rule per terminal or else it's a conflict
    for terminal, morphemes in nud.items():
      dedupedProductions = self._unique(morphemes, dedupe_func)
      if len(dedupedProductions) == 1:
        self.nud[terminal] = dedupedProductions[0].morphemes
        self.logger.debug('nud(%s) = %s' % (terminal, ', '.join([str(x) for x in self.nud[terminal]])))
      elif len(dedupedProductions) > 1:
        self.conflicts.append(NudConflict(terminal, [r.rule for r in dedupedProductions]))
    for terminal, morphemes in led.items():
      dedupedProductions = self._unique(morphemes, dedupe_func)
      if len(dedupedProductions) == 1:
        self.led[terminal] = dedupedProductions[0].morphemes
        self.logger.debug('led(%s) = %s' % (terminal, ', '.join([str(x) for x in self.led[terminal]])))
      elif len(dedupedProductions) > 1:
        self.conflicts.append(LedConflict(terminal, [r.rule for r in dedupedProductions]))
  
  def _unique(self, l, f):
    r = []
    for x in l:
      d = False
      for y in r:
        if f(x, y):
          d = True
      if not d:
        r.append(x)
    return r

class LL1Grammar(Grammar):
  def __init__(self, name, nonterminals, terminals, macros, rules, start, firstFollowCalc):
    super().__init__(name, rules)
    self.__dict__.update(locals())

    specials = {'_empty': EmptyString(-1), '_end': EndOfStream(-1)}
    for terminal in self.terminals:
      key = None
      if isinstance(terminal, EmptyString):
        key = '_empty'
      elif isinstance(terminal, EndOfStream):
        key = '_end'
      
      if key:
        del(specials[key])
        self.__dict__[key] = terminal
    
    for key, terminal in specials.items():
      self.terminals = self.terminals.union({terminal})
      self.__dict__[key] = terminal

    self._assignIds()
    (self.first, self.follow) = firstFollowCalc.compute(self)
    self._computeConflicts()
 
  # TODO: remove
  def getNormalizedRules(self, nonterminal = None):
    return self.getExpandedRules(self, nonterminal)
  
  def getStart(self):
    return self.start
  
  def _computeConflicts( self ):
    self.conflicts = []
    self.warnings = []
    nonterminalUsageMap = {N: list() for N in self.nonterminals} # maps nonterminal to rules that use this nonterminal in its production

    for R in self.expandedRules:
      for M in R.production.morphemes:
        if isinstance(M, NonTerminal):
          nonterminalUsageMap[M].append(R)

    for N in self.nonterminals:
      if self._empty in self.first[N] and len(self.first[N].intersection(self.follow[N])):
        self.conflicts.append( FirstFollowConflict( N, self.first[N], self.follow[N] ) )

      if not len(nonterminalUsageMap[N]) and not N.generated:
        self.warnings.append(UnusedNonterminalWarning(N))

      NR = self.getExpandedRules( N )
      if len(NR) == 0:
        self.conflicts.append( UndefinedNonterminalConflict(N) )
      for x in range(len(NR)):
        for y in range(len(NR)):
          if x == y:
            continue

          xR = self._pfirst(NR[x].production)
          yR = self._pfirst(NR[y].production)
          intersection = xR.intersection(yR.difference({self._empty}))
          if intersection != set():
            self.conflicts.append( FirstFirstConflict(NR[x], NR[y], self) )
    for macro in self.macros:
      if isinstance(macro, MorphemeListMacro):
        if self.first[macro.morpheme].intersection(self.follow[macro]) != set():
          self.conflicts.append( ListFirstFollowConflict(macro, self.first[macro.nonterminal], self.follow[macro]) )
    return self.conflicts

class CompositeGrammar(Grammar):
  def __init__( self, name, grammar, exprgrammars, lexer=Lexer() ):
    self.start = grammar.start

    rules = []
    expandedRules = []
    for rule in grammar.rules:
      if rule not in rules: rules.append(rule)
    for rule in grammar.expandedRules:
      if rule not in expandedRules: expandedRules.append(rule)
    for expr_grammar in exprgrammars:
      for rule in expr_grammar.rules:
        if rule not in rules: rules.append(rule)
      for rule in expr_grammar.expandedRules:
        if rule not in expandedRules: expandedRules.append(rule)

    super().__init__(name, rules)
    self.__dict__.update(locals())
    
    self.terminals = set(grammar.terminals)
    self.nonterminals = set(grammar.nonterminals)
    self._empty = grammar._empty
    self._end = grammar._end

    terminalIdMax = max(map(lambda x: x.id, self.terminals))
    self.expressionTerminals = dict()
    for i, exprGrammar in enumerate(self.exprgrammars):
      terminal = Terminal(exprGrammar.nonterminal.string.lower(), terminalIdMax + i)
      self.expressionTerminals[exprGrammar] = terminal
      self.terminals = self.terminals.union({terminal})
      grammar.first[exprGrammar.nonterminal] = {terminal}

    for exprgrammar in self.exprgrammars:
      for macros in exprgrammar.macros:
        for rule in macros.rules:
          if rule not in self.rules: self.rules.append(rule)
          if rule not in self.expandedRules: self.expandedRules.append(rule)
      tokens = exprgrammar.first[exprgrammar.nonterminal]
      grammar.first[exprgrammar.nonterminal] = grammar.first[exprgrammar.nonterminal].union(tokens)
      tokens = exprgrammar.follow[exprgrammar.nonterminal]
      grammar.follow[exprgrammar.nonterminal] = grammar.follow[exprgrammar.nonterminal].union(tokens)

    progress = True
    while progress:
      progress = False
      for exprgrammar in self.exprgrammars:
        progress |= exprgrammar.updateFirstFollow(grammar.first, grammar.follow)
        progress |= grammar.updateFirstFollow(exprgrammar.first, exprgrammar.follow)
    self.first = grammar.first
    self.follow = grammar.follow
    self.grammar._computeConflicts()

    self.conflicts = grammar.conflicts
    self.warnings = grammar.warnings
    for exprGrammar in self.exprgrammars:
      self.conflicts.extend(exprGrammar.conflicts)
    self.conflicts = list(filter(lambda x: type(x) not in [UndefinedNonterminalConflict], self.conflicts ))
    self.warnings = list(filter(lambda x: type(x) not in [UnusedNonterminalWarning], self.warnings ))

    for conflict in self.conflicts:
      if isinstance(conflict, FirstFirstConflict):
        conflict.grammar = self

    nonterminalUsageMap = {N: list() for N in self.nonterminals}
    for rule in self.getExpandedRules():
      if isinstance(rule, Rule):
        for morpheme in rule.production.morphemes:
          if isinstance(morpheme, NonTerminal):
            nonterminalUsageMap[morpheme].append(rule)
      if isinstance(rule, ExprRule):
        for production in [rule.nudProduction, rule.ledProduction]:
          for morpheme in production.morphemes:
            if isinstance(morpheme, NonTerminal):
              nonterminalUsageMap[morpheme].append(rule)

    for nonterminal in self.nonterminals:
      if not len(nonterminalUsageMap[nonterminal]) and not nonterminal.generated and nonterminal is not grammar.start:
        self.warnings.append(UnusedNonterminalWarning(nonterminal))

      nRules = self.getExpandedRules( nonterminal )
      if len(nRules) == 0 and nonterminal is not grammar.start and nonterminal not in [x.nonterminal for x in exprgrammars]:
        self.conflicts.append( UndefinedNonterminalConflict(nonterminal) )

    self._assignIds()

  def __getattr__(self, name):
    if name == 'll1_nonterminals':
      return [x for x in self.nonterminals if x not in [x.nonterminal for x in self.exprgrammars]]
    if name == 'standard_terminals':
      return self.getSimpleTerminals() 
    return self.__dict__[name]

  def getExpressionTerminal(self, exprGrammar):
    return self.expressionTerminals[exprGrammar]

  def getRuleFromFirstSet(self, nonterminal, first):
    rules = self.getExpandedLL1Rules(nonterminal)
    for rule in rules:
      if self._pfirst(rule.production).issuperset(first):
        return rule
    return None

  def getLL1Grammar(self):
    return self.grammar
  
  def getExpressionGrammars(self):
    return self.exprgrammars

  def getSimpleTerminals(self):
    return [terminal for terminal in self.terminals if terminal not in [self._empty, self._end]]

  def getExpandedLL1Rules(self, nonterminal = None):
    allRules = [rule for rule in self.expandedRules if isinstance(rule, Rule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

  def getLL1Rules(self, nonterminal = None):
    allRules = [rule for rule in self.rules if isinstance(rule, Rule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

  def getExpandedExpressionRules(self, nonterminal = None):
    allRules = [rule for rule in self.expandedRules if isinstance(rule, ExprRule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

  def getExpressionRules(self, nonterminal = None):
    allRules = [rule for rule in self.rules if isinstance(rule, ExprRule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

  def getNormalizedRules(self, nonterminal = None):
    return self.getExpandedLL1Rules(nonterminal)

  def str(self, theme=None):
    return self.__str__(theme)

  def __str__(self, theme=None):
    lexer = ''
    if self.lexer:
      lexer = '  lexer {\n    '
      if 'default' in self.lexer:
        for regex in self.lexer['default']:
          lexer += '\n    '.join(regex)
      lexer = self.lexer.str(theme=theme)
      lexer += '\n' if len(lexer) else ''

    rules = []
    for rule in self.grammar.rules:
      if isinstance(rule, Rule) and not isinstance(rule, MacroGeneratedRule):
        rules.append('    ' + str(rule))
    parser = '  parser<ll1> {\n'
    parser += '\n'.join(rules) + '\n'
    for grammar in self.exprgrammars:
      rules = []
      counter = 0
      for rule in grammar.rules:
        if not isinstance(rule, MacroGeneratedRule):
          precedence = ''
          if rule.operator:
            if rule.operator.binding_power > counter:
              counter = rule.operator.binding_power
              marker = '*'
            else:
              marker = '-'
            precedence = '({}:{}) '.format(marker, rule.operator.associativity)
          rules.append('      {}{}'.format(precedence, rule))
      parser += '    {0} = parser<expression> {{\n{1}\n    }}\n'.format(grammar.nonterminal.str(theme), '\n'.join(rules))
    parser += '  }'

    string = 'grammar {{\n{0}{1}\n}}'.format(
        lexer, parser 
    )
    return string

    rules = []
    for grammar in self.exprgrammars:
      for rule in grammar.rules:
        rules.append(str(rule))
      string += '\n    '.join(rules)
    return string
  
  def getParseTable( self ):
    nonterminals  = {n.id: n for n in self.nonterminals}
    terminals   = {t.id: t for t in self.getSimpleTerminals()}
    sort = lambda x: [x[key] for key in sorted(x.keys())]
    table = []
    for nonterminal in sort(nonterminals):
      rules = []
      for terminal in sort(terminals):
        next = None
        for rule in self.getExpandedLL1Rules(nonterminal):
          Fip = self._pfirst(rule.getProduction())
          if terminal in Fip or (self._empty in Fip and terminal in self.follow[nonterminal]):
            next = rule
            break
        rules.append(next)
      table.append(rules)
    return table

class LL1GrammarFactory:
  def create(self, name, nonterminals, terminals, macros, rules, start):
    return LL1Grammar(name, nonterminals, terminals, macros, rules, start, LL1FirstFollowCalculator())

class ExpressionGrammarFactory:
  def create(self, nonterminals, terminals, macros, rules, bindingPower, nonterminal):
    return ExpressionGrammar(nonterminals, terminals, macros, rules, bindingPower, nonterminal, ExpressionFirstFollowCalculator())
