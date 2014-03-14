from copy import copy, deepcopy
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
  def __eq__(self, other):
    for index, morpheme in enumerate(self.morphemes):
      try:
        if other.morhemes[index] != morpheme:
          return False
      except:
        return False
    return True
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
  def expand(self):
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
  def __getattr__(self, name):
    if name == 'must_consume_tokens':
      return len(self.production.morphemes) == 1 and self.production.morphemes[0] == EmptyString(-1)
    if name == 'morphemes':
      # TODO: This is only around because Grammar.__init__() needs it for making ExprRule and Rule both able to do this
      return self.production.morphemes
    return self.__dict__[name]

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
    return str(other) == str(self)

  def __hash__(self):
    return hash(str(self))

class MacroGeneratedRule(Rule):
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
    self.production = Production(nudProduction.morphemes + ledProduction.morphemes)
    if (not nudProduction or not len(nudProduction)) and \
       (not ledProduction or not len(ledProduction)):
      raise Exception('Rule must contain a NUD or a LED portion.')
    # TODO: this should be a conflict
    root = self.ledProduction.morphemes[0] if self.ledProduction and len(self.ledProduction) else None
    if root and not isinstance(root, Terminal):
      raise Exception('Root of expression rule must be a terminal.')
  def __copy__( self ):
    np = Production(copy(self.nudProduction.morphemes))
    lp = Production(copy(self.ledProduction.morphemes))
    return ExprRule(self.nonterminal, np, lp, self.nudAst, self.ast, self.operator)
  def __getattr__(self, name):
    if name == 'morphemes':
      all = []
      for morpheme in self.nudProduction.morphemes:
        all.append(morpheme)
      for morpheme in self.ledProduction.morphemes:
        all.append(morpheme)
      return all
    return self.__dict__[name]
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
      string = '{nt} = {nud}{nud_ast}'.format(nt=self.nonterminal, nud=self.nudProduction.str(theme), nud_ast=ast_to_str(self.nudAst))

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

class FirstFollowCalculator:
  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  # This is duplicated
  def _pfirst( self, grammar, P ):
    r = set()
    add_empty_token = True
    for m in P.morphemes:
      m_first_set = set([m]) if isinstance(m, Terminal) else self.first[m]
      if isinstance(m, MorphemeListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      toks = m_first_set.difference({grammar._empty})
      if len(toks) > 0:
        r = r.union(toks)
      if grammar._empty not in m_first_set:
        add_empty_token = False
        break
    if add_empty_token:
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
          self.logger.debug('RULE ' + str(rule))
          self.logger.debug('(1) first(%s) = {%s} ∪ {%s}' % (rule.nonterminal, ', '.join([str(x) for x in self.first[rule.nonterminal]]), morpheme))
          self.first[rule.nonterminal] = self.first[rule.nonterminal].union({morpheme})

        elif isinstance(morpheme, NonTerminal) or isinstance(morpheme, LL1ListMacro):
          add_empty_token = True
          for morpheme in rule.production.morphemes:
            if isinstance(morpheme, LL1ListMacro):
              sub = self.first[morpheme.start_nt]
            elif isinstance(morpheme, Terminal):
              sub = set([morpheme])
            else:
              sub = self.first[morpheme]
            if not self.first[rule.nonterminal].issuperset(sub.difference({grammar._empty})):
              progress = changed = True
              self.logger.debug('RULE ' + str(rule))
              self.logger.debug('(2) first(%s) = {%s} ∪ {%s}' % ( \
                        rule.nonterminal, \
                        ', '.join([str(x) for x in self.first[rule.nonterminal]]), \
                        ', '.join([str(x) for x in sub.difference({grammar._empty})]) \
                      ))
              self.first[rule.nonterminal] = self.first[rule.nonterminal].union(sub.difference({grammar._empty}))
            if grammar._empty not in sub:
              add_empty_token = False
              break
          if add_empty_token:
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
            next_first_set = set([nextToken]) if isinstance(nextToken, Terminal) else self.first[nextToken].difference({grammar._empty})
            if not self.follow[morpheme].issuperset(next_first_set):
              progress = changed = True
              self.logger.debug('follow(%s) = {%s} ∪ {%s}' % ( \
                morpheme, \
                ', '.join([str(x) for x in self.follow[morpheme]]), \
                ', '.join([str(x) for x in next_first_set]) \
              ))
              self.follow[morpheme] = self.follow[morpheme].union(next_first_set)

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
    nonterminals = grammar.nonterminals + [grammar.nonterminal]
    self.first = {x: set() for x in nonterminals}
    self.follow = {x: set() for x in nonterminals}
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

    for rule in self.rules:
      for expanded_rule in rule.expand():
        if expanded_rule.nonterminal not in self.nonterminals:
          self.nonterminals.append(expanded_rule.nonterminal)
        for morpheme in expanded_rule.morphemes:
          if isinstance(morpheme, Terminal) and morpheme not in self.terminals:
            self.terminals.append(morpheme)
          if isinstance(morpheme, NonTerminal) and morpheme not in self.nonterminals:
            self.nonterminals.append(morpheme)

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
    morphemes = {}
    i = 0
    for terminal in self.terminals:
      if self.isSimpleTerminal(terminal):
        terminal.id = i
        morphemes[str(terminal)] = terminal.id
        i += 1
    for nonterminal in self.nonterminals:
      nonterminal.id = i
      morphemes[str(nonterminal)] = nonterminal.id
      i += 1

    for rule_set in [self.rules, self.expandedRules]:
      for i, rule in enumerate(rule_set):
        rule.id = i
        if isinstance(rule, Rule):
          for morpheme in rule.production.morphemes:
            if str(morpheme) in morphemes:
              morpheme.id = morphemes[str(morpheme)]
        if isinstance(rule, ExprRule):
          for morpheme in rule.nudProduction.morphemes:
            if str(morpheme) in morphemes:
              morpheme.id = morphemes[str(morpheme)]
          for morpheme in rule.ledProduction.morphemes:
            if str(morpheme) in morphemes:
              morpheme.id = morphemes[str(morpheme)]

  def must_consume_tokens(self, nonterminal):
    for rule in self.getExpandedLL1Rules(nonterminal):
      if rule.must_consume_tokens:
        return True
    return False

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
 
  def ruleFirst(self, rule):
    return self._pfirst(rule.production)

  # These should be pre-calculated.  also this is duplicated
  def _pfirst( self, P ):
    r = set()
    add_empty_token = True
    for m in P.morphemes:
      if isinstance(m, MorphemeListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      m_first_set = set([m]) if isinstance(m, Terminal) else self.first[m]
      toks = m_first_set.difference({self._empty})
      if len(toks) > 0:
        r = r.union(toks)
      if self._empty not in m_first_set:
        add_empty_token = False
        break
    if add_empty_token:
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
  
class ExpressionGrammar(Grammar):
  def __init__(self, macros, rules, precedence, nonterminal, firstFollowCalc=ExpressionFirstFollowCalculator()):
    if not isinstance(rules, list):
      raise Exception("Expression grammar expecting an ordered list of rules to express operator precedence.")
    super().__init__('expr', rules) # TODO: fix this first parameter
    self.__dict__.update(locals())
    self._assignIds()
    self.computedPrecedence = precedence # Must be dictionary
    (self.first, self.follow) = firstFollowCalc.compute(self)
    self._compute_conflicts()
 
  def ruleFirst(self, rule):
    if len(rule.nudProduction) and rule.nudProduction.morphemes[0] != rule.nonterminal:
      return self._pfirst(rule.nudProduction)
    return set()
  
  def _compute_conflicts( self ):
    nud = {}
    led = {}
    self.conflicts = []

    for rule in self.expandedRules:
      if isinstance(rule, ExprRule):
        # For 'mixfix' rules... make sure no two nud/led functions start with the same thing.
        if rule.operator is None and len(rule.nudProduction):
          morpheme = rule.nudProduction.morphemes[0]
          if morpheme not in nud:
            nud[morpheme] = list()
          if len(nud[morpheme]):
            self.conflicts.append(NudConflict(morpheme, [rule] + nud[morpheme]))
          nud[morpheme].append(rule)
        if len(rule.ledProduction):
          # TODO: no test for this code path
          morpheme = rule.nudProduction.morphemes[0]
          if morpheme not in led:
            led[morpheme] = list()
          if rule in led[morpheme]:
            self.conflicts.append(NudConflict(morpheme, [rule] + led[morpheme]))
          led[morpheme].append(rule)

class LL1Grammar(Grammar):
  def __init__(self, name, macros, rules, start, firstFollowCalc=LL1FirstFollowCalculator()):
    super().__init__(name, rules)
    self.__dict__.update(locals())
    
    for terminal in [EmptyString(-1), EndOfStream(-1)]:
      if terminal not in self.terminals:
        self.terminals.append(terminal)

    self._assignIds()
    (self.first, self.follow) = firstFollowCalc.compute(self)
    self._compute_conflicts()
  
  def getStart(self):
    return self.start
  
  def _compute_conflicts( self ):
    self.conflicts = []
    self.warnings = []
    nonterminal_rules = {str(n): list() for n in self.nonterminals} # maps nonterminal to rules that use this nonterminal in its production

    for rule in self.expandedRules:
      for morpheme in rule.morphemes:
        if isinstance(morpheme, NonTerminal):
          nonterminal_rules[str(morpheme)].append(rule)

    for N in self.nonterminals:
      if self._empty in self.first[N] and len(self.first[N].intersection(self.follow[N])):
        self.conflicts.append( FirstFollowConflict( N, self.first[N], self.follow[N] ) )

      if not len(nonterminal_rules[str(N)]) and not N.generated and N != self.start:
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
  def __init__( self, name, grammar, exprgrammars, lexer=Lexer(), firstFollowCalc=LL1FirstFollowCalculator() ):
    self.__dict__.update(locals())
    self.start = grammar.start

    rules = OrderedDict()
    for rule in grammar.rules: rules[str(rule)] = rule
    for expression_grammar in exprgrammars:
      for rule in expression_grammar.rules: rules[str(rule)] = rule

    super().__init__(name, list(rules.values()))

    def add_terminal(terminal):
      if terminal not in self.terminals:
        self.terminals.append(terminal)
    def add_nonterminal(nonterminal):
      if nonterminal not in self.nonterminals:
        self.nonterminals.append(nonterminal)
    
    self.terminals = list(grammar.terminals)
    self.nonterminals = list(grammar.nonterminals)

    rule_str = OrderedDict([(str(r), r) for r in self.rules])
    expanded_rule_str = OrderedDict([(str(r), r) for r in self.expandedRules])
    self.grammar_rules = OrderedDict()
    self.grammar_expanded_rules = OrderedDict()
    self.grammar_rules[grammar] = list()
    self.grammar_expanded_rules[grammar] = list()
    for rule in self.grammar.rules:
      self.grammar_rules[grammar].append(rule_str[str(rule)])
    for rule in self.grammar.expandedRules:
      self.grammar_expanded_rules[grammar].append(expanded_rule_str[str(rule)])
    for grammar in self.exprgrammars:
      self.grammar_rules[grammar] = list()
      self.grammar_expanded_rules[grammar] = list()
      for rule in grammar.rules:
        self.grammar_rules[grammar].append(rule_str[str(rule)])
      for rule in grammar.expandedRules:
        self.grammar_expanded_rules[grammar].append(expanded_rule_str[str(rule)])

    max_terminal_id = max(map(lambda x: x.id, self.terminals))
    self.expressionTerminals = dict()
    for index, expr_grammar in enumerate(self.exprgrammars):
      # TODO: make this terminal an abstract terminal.  Prefix with underscore.  Lots of tests fail if either of these changes are made
      terminal = Terminal(expr_grammar.nonterminal.string.lower(), max_terminal_id + index)
      self.expressionTerminals[expr_grammar] = terminal
      expr_grammar.first[expr_grammar.nonterminal] = expr_grammar.first[expr_grammar.nonterminal].union({terminal})
      add_terminal(terminal)
      for terminal in expr_grammar.terminals:
        add_terminal(terminal)
      for nonterminal in expr_grammar.nonterminals:
        add_nonterminal(nonterminal)

    self.first = copy(self.grammar.first)
    self.follow = copy(self.grammar.follow)
    for expr_grammar in self.exprgrammars:
      expr_nt = expr_grammar.nonterminal
      self.first[expr_nt] = self.first[expr_nt].union(expr_grammar.first[expr_nt])
      self.follow[expr_nt] = self.follow[expr_nt].union(expr_grammar.follow[expr_nt])

    self.firstFollowCalc.first = self.first
    self.firstFollowCalc.follow = self.follow
    progress = True
    while progress:
      progress = False
      for expr_grammar in self.exprgrammars:
        progress |= self.updateFirstFollow(expr_grammar.first, expr_grammar.follow)
    self.grammar._compute_conflicts()

    self.conflicts = self.grammar.conflicts
    self.warnings = self.grammar.warnings
    for exprGrammar in self.exprgrammars:
      self.conflicts.extend(exprGrammar.conflicts)
    self.conflicts = list(filter(lambda x: type(x) not in [UndefinedNonterminalConflict], self.conflicts ))
    self.warnings = list(filter(lambda x: type(x) not in [UnusedNonterminalWarning], self.warnings ))

    for conflict in self.conflicts:
      if isinstance(conflict, FirstFirstConflict):
        conflict.grammar = self

    nonterminal_rules = {str(n): list() for n in self.nonterminals}
    for rule in self.getExpandedRules():
      for morpheme in rule.morphemes:
        if isinstance(morpheme, NonTerminal):
          nonterminal_rules[str(morpheme)].append(rule)

    for nonterminal in self.nonterminals:
      if not len(nonterminal_rules[str(nonterminal)]) and not nonterminal.generated and nonterminal is not self.start:
        self.warnings.append(UnusedNonterminalWarning(nonterminal))

      nRules = self.getExpandedRules( nonterminal )
      if len(nRules) == 0 and nonterminal is not grammar.start and nonterminal not in [x.nonterminal for x in exprgrammars]:
        self.conflicts.append( UndefinedNonterminalConflict(nonterminal) )
    self._assignIds()

  def __getattr__(self, name):
    if name == 'll1_nonterminals':
      return [x for x in self.nonterminals if x not in [x.nonterminal for x in self.exprgrammars]]
    elif name == 'standard_terminals':
      return [terminal for terminal in self.terminals if terminal not in [self._empty, self._end]]
    elif name == 'grammar_expanded_rules':
      return self.__dict__['grammar_expanded_rules']
    elif name == 'grammar_expanded_expr_rules':
      grammar_rules = {}
      for grammar, rules in self.grammar_expanded_rules.items():
        grammar_rules[grammar] = list(filter(lambda x: isinstance(x, ExprRule), rules))
      return grammar_rules
    elif name == 'parse_table':
      if 'parse_table' in self.__dict__:
        return self.__dict__['parse_table']
      nonterminals  = {n.id: n for n in self.nonterminals}
      terminals   = {t.id: t for t in self.standard_terminals}
      sort = lambda x: [x[key] for key in sorted(x.keys())]
      table = []
      for nonterminal in sort(nonterminals):
        rules = []
        for terminal in sort(terminals):
          next = None
          for rule in self.getExpandedLL1Rules(nonterminal):
            Fip = self._pfirst(rule.production)
            if terminal in Fip or (self._empty in Fip and terminal in self.follow[nonterminal]):
              next = rule
              break
          rules.append(next)
        table.append(rules)
      self.__dict__['parse_table'] = table
      return table
    else:
      return self.__dict__[name]

  def ruleFirst(self, rule):
    if isinstance(rule, ExprRule):
      if len(rule.nudProduction) and rule.nudProduction.morphemes[0] != rule.nonterminal:
        return self._pfirst(rule.nudProduction)
    return self._pfirst(rule.production)

  def getExpressionTerminal(self, exprGrammar):
    return self.expressionTerminals[exprGrammar]

  def getRuleFromFirstSet(self, nonterminal, first):
    rules = self.getExpandedLL1Rules(nonterminal)
    for rule in rules:
      if self._pfirst(rule.production).issuperset(first):
        return rule
    return None

  def getExpandedLL1Rules(self, nonterminal = None):
    allRules = [rule for rule in self.expandedRules if isinstance(rule, Rule)]
    if nonterminal:
      return [rule for rule in allRules if str(rule.nonterminal) == str(nonterminal)]
    return allRules 

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
