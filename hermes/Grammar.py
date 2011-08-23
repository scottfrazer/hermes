from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Expression
from hermes.Morpheme import Morpheme, AbstractTerminal
from hermes.Conflict import FirstFirstConflict, FirstFollowConflict, ListFirstFollowConflict, NudConflict, LedConflict
from hermes.Macro import ListMacro, LL1ListMacro, ExprListMacro, SeparatedListMacro, NonterminalListMacro
from hermes.Logger import Factory as LoggerFactory

moduleLogger = LoggerFactory().getModuleLogger(__name__)

class Production:
  def __init__( self, morphemes ):
    self.morphemes = morphemes
  def __str__( self ):
    return " ".join([str(p) for p in self.morphemes])

class Rule:
  def __init__( self, nonterminal, production, id=None, root=None, ast=None):
    self.nonterminal = nonterminal
    self.production = production
    self.id = id
    self.root = root
    self.ast = ast
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
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
    self.logger.debug('Expand Rule %s => %s' % (self, ', '.join([str(x) for x in rules])))
    return rules
  
  def __str__( self ):
    return "%s := %s" % (str(self.nonterminal), str(self.production))
  

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
  def __repr__( self ):
    return self.name + '( ' + ', '.join(['%s=$%s' % (k,str(v)) for k,v in self.parameters.items()]) + ' )' 

class AstTranslation:
  def __init__( self, idx ):
    self.idx = idx
  def __repr__( self ):
    return '$'+str(self.idx)

class ExprRule:
  def __init__(self, type, atoms, rule):
    self.type = type
    self.atoms = atoms
    self.rule = rule
  def __str__(self):
    return "(ExprRule: '%s', [%s], (Rule: %s))" % (self.type, ', '.join([str(x) for x in self.atoms]), str(self.rule))

class OperatorPrecedence:
  def __init__(self, terminal, precedence, associativity):
    self.__dict__.update(locals())
  
  def __str__(self):
    return 'OperatorPrecedence(%s, %s, %s)' % (str(self.terminal), self.precedence, self.associativity)
  


# Important note on first/follow sets
#
# 1) LL(1) Grammar will treat any nonterminal in a grammar without a rule 
#    defining its productions as an opaque, non epsilon yielding nonterminal,
#    but only for the purposes of calculating first/follow sets.
#
# 2) A corollary to this is that an ExpressionGrammar should consume one or more
#    tokens.
#
# 3) Expression grammars and LL(1) grammars both compute first and follow the 
#    same.
#
# 4) The union of single LL(1) grammar and n Expression grammars is a
#    CompoundGrammar.  The CompoundGrammar will union in a `λ` terminal into the
#    first sets of each of the n Expression grammar's `nonterminal` which is
#    exposes to the LL(1) parser.  Then, _computeFirst and _computeFollow are
#
# 5) first(infix) = {} and follow(infix) = {}. all other expression rules follow
#    the normal algorithm.  This means that any infix operator is essentially
#    invisible to the LL(1) grammar.

class Grammar:
  ε = EmptyString(-1)
  λ = Expression(-1)
  σ = EndOfStream(-1)
  terminals = []
  nonterminals = []
  rules = set()
  nrules = set()
  conflicts = []
  firstSet = None
  followSet = None
  start = None
  tLookup = None
  ntLookup = None

  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)

  def isSimpleTerminal( self, t ):
    return isinstance(t, Terminal) and not isinstance(t, AbstractTerminal)
  
  def isSpecialTerminal( self, t ):
    return isinstance(t, AbstractTerminal)
  
  def isTerminal( self, t ):
    return isinstance(t, Terminal)
  
  def isNonTerminal( self, n ):
    return isinstance(n, NonTerminal)
  
  # TODO: remove
  def _getAtomVarName( self, atom ):
    if isinstance(atom, Terminal):
      return "TERMINAL_" + str(atom).strip("'").upper()
    if isinstance(atom, NonTerminal):
      return "NONTERMINAL_" + str(atom).upper()

  def first( self, nonterminal = None ):
    if not self.firstSet:
      self._initFirst()
      self._computeFirst()
    if nonterminal:
      return self.firstSet[nonterminal]
    return self.firstSet
  
  def follow( self, nonterminal = None ):
    if not self.followSet:
      self._initFollow()
      self._computeFollow()
    if nonterminal:
      return self.followSet[nonterminal]
    return self.followSet
  
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
  
  def _initFirst( self ):
    self.firstSet = dict()
    for N in self.nonterminals:
      self.firstSet[N] = set()
    for N in self.terminals:
      self.firstSet[N] = {N}
    # TODO: ???
    for M in self.macros:
      if isinstance(M, LL1ListMacro):
          self.firstSet[M] = set()
    for R in self.rules:
      if len(R.production.morphemes) == 1 and self.ε in R.production.morphemes:
        self.firstSet[R.nonterminal].union({self.ε})
  
  def _initFollow( self ):
    self.followSet = dict()

    for N in self.nonterminals:
      self.followSet[N] = set()
    for M in self.macros:
      self.followSet[M] = set()

    if self.start:
      self.followSet[ self.start ] = {self.σ}
  
  def _computeFirst( self, excludedRuleIds = [] ):
    expander = RuleExpander(self.rules)
    rules = set(expander.expand())

    progress = True
    while progress == True:
      progress = False
      for R in rules:
        morpheme = R.production.morphemes[0]

        # TODO: filter out extraneous ε's in grammar files (e.g. x := ε + 'a' + ε)
        # For now, assume that it's in correct form.  Also, fix this stupid if statement!!
        if (type(morpheme) is Terminal or type(morpheme) is EmptyString) and \
           morpheme not in self.firstSet[R.nonterminal]:
          progress = True
          self.logger.debug('first(%s) = {%s} ∪ {%s}' % (R.nonterminal, ', '.join([str(x) for x in self.firstSet[R.nonterminal]]), morpheme))
          self.firstSet[R.nonterminal] = self.firstSet[R.nonterminal].union({morpheme})

        # TODO: WOW this is bad.  fix when tests are passing.
        elif isinstance(morpheme, NonTerminal) or \
             isinstance(morpheme, LL1ListMacro):
          for x in range(len(R.production.morphemes)):
            M = R.production.morphemes[x]
            if isinstance(M, LL1ListMacro):
              sub = self.firstSet[M.start_nt]
            else:
              sub = self.firstSet[M]
            if not self.firstSet[R.nonterminal].issuperset(sub.difference({self.ε})):
              progress = True
            self.logger.debug('first(%s) = {%s} ∪ {%s}' % ( \
                      R.nonterminal, \
                      ', '.join([str(x) for x in self.firstSet[R.nonterminal]]), \
                      ', '.join([str(x) for x in sub.difference({self.ε})]) \
                    ))
            self.firstSet[R.nonterminal] = self.firstSet[R.nonterminal].union(sub.difference({self.ε}))
            if self.ε not in sub:
              break
    return self.firstSet
  
  def _computeFollow( self, excludedRuleIds = [] ):
    expander = RuleExpander(self.rules)
    rules = set(expander.expand())
    
    progress = True
    while progress == True:
      progress = False

      for R in rules:
        if R.id in excludedRuleIds:
          continue

        for x in range(len(R.production.morphemes)):
          morpheme = R.production.morphemes[x]

          if type(morpheme) is Terminal or type(morpheme) is EmptyString:
            continue

          if isinstance(morpheme, LL1ListMacro):
            morpheme = morpheme.start_nt

          n = None
          if x < len(R.production.morphemes) - 1:
            n = R.production.morphemes[x+1]
            if isinstance(n, LL1ListMacro):
              n = n.start_nt
          if n:
            nsyms = self.firstSet[n].difference({self.ε})
            if not self.followSet[morpheme].issuperset(nsyms):
              progress = True
              self.logger.debug('follow(%s) = {%s} ∪ {%s}' % ( \
                morpheme, \
                ', '.join([str(x) for x in self.followSet[morpheme]]), \
                ', '.join([str(x) for x in nsyms]) \
              ))
              self.followSet[morpheme] = self.followSet[morpheme].union(nsyms)
          if not n or self.ε in self.firstSet[n]:
            z = self.followSet[R.nonterminal]
            y = self.followSet[morpheme]

            if not y.issuperset(z):
              progress = True
              self.logger.debug('follow(%s) = {%s} ∪ {%s}' % ( \
                morpheme, \
                ', '.join([str(x) for x in y]), \
                ', '.join([str(x) for x in z]) \
              ))
              self.followSet[morpheme] = y.union(z)
    return self.followSet
  
  # These should be pre-calculated.
  def _pfirst( self, P ):
    r = set()
    for m in P.morphemes:
      if isinstance(m, NonterminalListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      toks = self.first(m).difference({self.ε})
      if len(toks) > 0:
        r = r.union(toks)
      if self.ε not in self.first(m):
        break
    return r
  
  def _ntrules( self, n ):
    return [rule for rule in self.nrules if str(rule.nonterminal) == str(n)]
  

class ExpressionGrammar(Grammar):
  def __init__(self, nonterminals, terminals, macros, rules, precedence, nonterminal):
    self.__dict__.update(locals())
    super().__init__()
    self._assignIds()
    self._computePrecedence()
    infixRuleIds = [r.id for r in self.rules if self.isInfixRule(r)]
    self._initFirst()
    self._computeFirst( excludedRuleIds=infixRuleIds )
    self._initFollow()
    self._computeFollow( excludedRuleIds=infixRuleIds )
    self._computeConflicts()
  
  def addParent( self, parent ):
    self.firstSet.update( parent.first().items() )
    self.followSet.update( parent.follow().items() )
    self._computeFirst()
    self._computeFollow()
  
  def _assignIds(self):
    for i, rule in enumerate(self.rules):
      rule.id = i
  
  def _computePrecedence(self):
    counter = 1000
    self.computedPrecedence = {}
    for precedence in self.precedence:
      for terminal in precedence['terminals']:
        if terminal not in self.computedPrecedence:
          self.computedPrecedence[terminal] = list()
        self.computedPrecedence[terminal].append( OperatorPrecedence(terminal, counter, precedence['associativity']) )
      counter += 1000
  
  def isInfixRule( self, rule ):
    atoms = rule.production.morphemes
    return len(atoms) == 3 and \
       rule.nonterminal.string.lower() == '_expr' and \
       atoms[0] == rule.nonterminal and isinstance(atoms[1], Terminal) and atoms[2] == rule.nonterminal
  
  def isPrefixRule( self, rule ):
    atoms = rule.production.morphemes
    return len(atoms) == 2 and \
       rule.nonterminal.string.lower() == '_expr' and \
       atoms[1] == rule.nonterminal and isinstance(atoms[0], Terminal)
  
  def isPrimitiveExprRule( self, rule ):
    return len(rule.production.morphemes) == 1
  
  def getPrecedence(self):
    return self.computedPrecedence
  
  def _computeConflicts( self ):
    nud = {}
    led = {}
    self.conflicts = []
    dedupe_func = lambda x, y: (x.type==y.type and (x.type == 'nonterminal' or x.type=='symbol'))
    morphemes = set(self.terminals).union(set(self.nonterminals))
    for m in morphemes:
      nud[m] = []
      led[m] = []
    for e in self.rules:
      if self.isInfixRule(e):
        led[e.production.morphemes[1]].append(ExprRule('infix', [], e))
      elif self.isPrefixRule(e):
        nud[e.production.morphemes[0]].append(ExprRule('prefix', [], e))
      elif self.isPrimitiveExprRule(e):
        nud[e.production.morphemes[0]].append(ExprRule('symbol', [], e))
      else:
        if e.root == 0:
          a = e.production.morphemes
          nud[a[0]].append(ExprRule(self._r2d2(a), a, e))
        elif e.root == 1:
          a = e.production.morphemes[0]
          nud[a].append(ExprRule(self._r2d2(a), [a], e))
        else:
          raise Exception('not supported, yet.')
        b = e.production.morphemes[1:]
        if e.root == 1:
          led[b[0]].append(ExprRule(self._r2d2(b), b, e))
    
    self.nud = {}
    self.led = {}
    for t, r in nud.items():
      u = self._unique(r, dedupe_func)
      if len(u) > 0:
        self.nud[t] = u[0]

    for t, r in led.items():
      u = self._unique(r, dedupe_func)
      if len(u) > 0:
        self.led[t] = u[0]

    for terminal, rules in nud.items():
      rules = self._unique(rules, dedupe_func)
      if len(rules) > 1:
        self.conflicts.append(NudConflict(terminal, [r.rule for r in rules]))
    for terminal, rules in led.items():
      rules = self._unique(rules, dedupe_func)
      if len(rules) > 1:
        self.conflicts.append(LedConflict(terminal, [r.rule for r in rules]))
  
  # Beep-boop
  def _r2d2(self, a):
    if isinstance(a, Terminal):
      return 'symbol'
    elif isinstance(a, NonTerminal):
      return 'nonterminal'
    elif isinstance(a, ExprListMacro):
      return 'list'
    elif isinstance(a, list):
      return 'mixfix'
    return None
  
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
  def __init__(self, nonterminals, terminals, macros, rules, start):
    super().__init__()
    self.__dict__.update(locals())
    
    specials = {'ε': EmptyString(-1), 'λ': Expression(-1), 'σ': EndOfStream(-1)}
    for terminal in self.terminals:
      key = None
      if isinstance(terminal, EmptyString):
        key = 'ε'
      elif isinstance(terminal, Expression):
        key = 'λ'
      elif isinstance(terminal, EndOfStream):
        key = 'σ'
      
      if key:
        del(specials[key])
        self.__dict__[key] = terminal
    
    for key, terminal in specials.items():
      self.terminals = self.terminals.union({terminal})
      self.__dict__[key] = terminal
    
    self.nrules = self._normalize(self.rules.copy())
    self._assignIds()
    self._initFirst()
    self._computeFirst()
    self._initFollow()
    self._computeFollow()
    self._computeConflicts()
  
  def getRules(self):
    return self.rules
  
  def getNormalizedRules(self):
    return self.nrules
  
  def getStart(self):
    return self.start
  
  def _assignIds(self):
    i = 0
    for terminal in self.terminals:
      if self.isSimpleTerminal(terminal):
        terminal.id = i
        i += 1
    for nonterminal in self.nonterminals:
      nonterminal.id = i
      i += 1

    for ruleSet in [self.rules, self.nrules]:
      for i, rule in enumerate(ruleSet):
        rule.id = i
  
  def _computeConflicts( self ):
    self.conflicts = []
    for N in self.nonterminals:
      if self.ε in self.first(N) and len(self.first(N).intersection(self.follow(N))):
        self.conflicts.append( FirstFollowConflict( N, self.first(N), self.follow(N) ) )

      NR = self._ntrules( N )
      for x in range(len(NR)):
        for y in range(len(NR)):
          if x == y:
            continue

          xR = self._pfirst(NR[x].production)
          yR = self._pfirst(NR[y].production)
          intersection = xR.intersection(yR)
          if intersection != set():
            self.conflicts.append( FirstFirstConflict(NR[x], xR, NR[y], yR) )
    for macro in self.macros:
      if isinstance(macro, NonterminalListMacro):
        if self.firstSet[macro.nonterminal].intersection(self.followSet[macro]) != set():
          self.conflicts.append( ListFirstFollowConflict(macro, self.firstSet[macro.nonterminal], self.followSet[macro]) )
    return self.conflicts
  
  def _normalize( self, rules ):
    nrules = list()
    for expanded in map(lambda x: x.expand(), rules):
      for e in expanded:
        nrules.append(e)
    return set(nrules)
  
  def __str__( self, normalize = True ):
    if normalize:
      rules = self.normalized()
    else:
      rules = self.rules
    return "\n".join([ str(r) for r in rules ])
  

class CompositeGrammar(Grammar):
  def __init__( self, grammar, exprgrammars ):
    if not isinstance(exprgrammars, list):
      raise Exception('parameter 2 must be a list')

    super().__init__()
    self.__dict__.update(locals())
    
    # Simply by convention am I combining all the terminals and nonterminals
    # and passing it to  all of the grammars.  It's more information than it
    # needs, but easier to manage.
    self.terminals = grammar.terminals
    self.nonterminals = grammar.nonterminals
    self.rules = grammar.rules
    self.ε = grammar.ε
    self.λ = grammar.λ
    self.σ = grammar.σ
    for exprgrammar in self.exprgrammars:
      self.rules = self.rules.union(exprgrammar.rules)
      tokens = exprgrammar.first(exprgrammar.nonterminal).union({self.λ})
      grammar.firstSet[exprgrammar.nonterminal] = grammar.firstSet[exprgrammar.nonterminal].union(tokens)
      tokens = exprgrammar.follow(exprgrammar.nonterminal)
      grammar.followSet[exprgrammar.nonterminal] = grammar.followSet[exprgrammar.nonterminal].union(tokens)
    self.conflicts = grammar.conflicts
    for exprgrammar in self.exprgrammars:
      exprgrammar.addParent(grammar)
      self.conflicts.extend(exprgrammar.conflicts)
    grammar._computeFirst()
    grammar._computeFollow()
  
  def first(self, nonterminal = None):
    return self.grammar.first(nonterminal)
  
  def follow(self, nonterminal = None):
    return self.grammar.follow(nonterminal)
  
  def getLL1Grammar(self):
    return self.grammar
  
  def getExpressionGrammars(self):
    return self.exprgrammars
  
  def getLL1Rules(self):
    return self.grammar.getRules()
  
  def getNormalizedLL1Rules(self):
    return self.grammar.getNormalizedRules()
  
  # These three functions are coupled
  def _compute_parse_table( self ):
    terminals = self._strip_abstract_terminals( self.terminals.copy() )
    NT  = {n.id: n for n in self.nonterminals}
    T   = {t.id: t for t in terminals}
    tab = []
    for N in self._sort_dict(NT):
      rules = []
      for t in self._sort_dict(T):
        next = None
        for R in self.getLL1Grammar()._ntrules(N):
          Fip = self._pfirst(R.production)
          if t in Fip or (self.ε in Fip and t in self.follow[N]):
            next = R
            break
        rules.append(next)
      tab.append(rules)
    return tab
  
  def _sort_dict(self, a):
    return [a[key] for key in sorted(a.keys())]
  
  def _strip_abstract_terminals( self, terminals ):
    new = []
    for terminal in terminals: #['λ', 'ε', 'σ']:
      if str(terminal) not in ['λ', 'ε', 'σ']:
        new.append(terminal)
    return new
  
