from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Expression
from hermes.Morpheme import Morpheme
from hermes.Conflict import FirstFirstConflict, FirstFollowConflict, ListFirstFollowConflict, NudConflict, LedConflict
from hermes.Macro import ListMacro, LL1ListMacro, ExprListMacro, SeparatedListMacro, NonterminalListMacro

class Production:
  def __init__( self, morphemes ):
    self.morphemes = morphemes
  def __str__( self ):
    return " ".join([str(p) for p in self.morphemes])

class Rule:
  def __init__( self, nonterminal, production, id, root, ast = None):
    self.nonterminal = nonterminal
    self.production = production
    self.id = id
    self.root = root
    self.ast = ast
  def expand( self ):
    morphemes = []
    rules = []
    for m in self.production.morphemes:
      if isinstance(m, SeparatedListMacro) or isinstance(m, NonterminalListMacro):
        rules.extend(m.rules)
        morphemes.append(m.start_nt)
      else:
        morphemes.append(m)
    rules.append(Rule(self.nonterminal, Production(morphemes), self.id, self.root, self.ast))
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

class Grammar:

  # Special Terminals
  ε = EmptyString(0)
  λ = Expression(1)
  σ = EndOfStream(2)

  # Internal
  def _compute_first( self ):
    self.first = dict()
    for s,N in self.nonterminals.items():
      if s.lower() == '_expr':
        self.first[N] = {self.λ}
      else:
        self.first[N] = set()
    for s,N in self.terminals.items():
      self.first[N] = {N}
    for M in self.macros:
      if isinstance(M, NonterminalListMacro) or isinstance(M, SeparatedListMacro):
        if str(M.start_nt).lower() == '_expr':
          self.first[M] = {self.λ}
        else:
          self.first[M] = set()
    for R in self.rules:
      if len(R.production.morphemes) == 1 and self.ε in R.production.morphemes:
        self.first[R.nonterminal].union({self.ε})

    expander = RuleExpander(self.rules)
    rules = set(expander.expand()).union(self.exprRules)

    progress = True
    while progress == True:
      progress = False
      for R in rules:
        morpheme = R.production.morphemes[0]

        if (type(morpheme) is Terminal or type(morpheme) is EmptyString) and morpheme not in self.first[R.nonterminal]:
          progress = True
          self.first[R.nonterminal] = self.first[R.nonterminal].union({morpheme})

        elif type(morpheme) is NonTerminal and morpheme.string.lower() == '_expr' and self.λ not in self.first[R.nonterminal]:
          progress = True
          self.first[R.nonterminal] = self.first[R.nonterminal].union({self.λ})

        elif isinstance(morpheme, NonTerminal) or isinstance(morpheme, NonterminalListMacro) or isinstance(morpheme, SeparatedListMacro):
          for x in range(len(R.production.morphemes)):
            M = R.production.morphemes[x]
            if isinstance(M, NonterminalListMacro) or isinstance(M, SeparatedListMacro):
              sub = self.first[M.start_nt]
            else:
              sub = self.first[M]
            if not self.first[R.nonterminal].issuperset(sub.difference({self.ε})):
              progress = True
            self.first[R.nonterminal] = self.first[R.nonterminal].union(sub.difference({self.ε}))
            if self.ε not in sub:
              break
    return self.first
  
  def _compute_follow( self ):
    self.follow = dict()

    for s,N in self.nonterminals.items():
      self.follow[N] = set()
    for M in self.macros:
      self.follow[M] = set()

    self.follow[ self.start ] = {self.σ}

    expander = RuleExpander(self.rules)
    rules = set(expander.expand()).union(self.exprRules)

    progress = True
    while progress == True:
      progress = False

      for R in rules:
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
            nsyms = self.first[n].difference({self.ε})
            if not self.follow[morpheme].issuperset(nsyms):
              progress = True
              self.follow[morpheme] = self.follow[morpheme].union(nsyms)
          if not n or self.ε in self.first[n]:
            z = self.follow[R.nonterminal]
            y = self.follow[morpheme]

            if not y.issuperset(z):
              progress = True
              self.follow[morpheme] = y.union(z)

    for i, R in enumerate(self.rules):
      for j, atom in enumerate(R.production.morphemes):
        if isinstance(atom, NonterminalListMacro):
          try:
            pass
            self.follow[atom].union({self.first[R.production.morphemes[j+1]]})
          except:
            pass # Might need to do : atom.first = atom.first ∪ {ε}?
    return self.follow
  
  def _pfirst( self, P ):
    r = set()
    for m in P.morphemes:
      if isinstance(m, NonterminalListMacro) or isinstance(m, SeparatedListMacro):
        m = m.start_nt
      toks = self.first[m].difference({self.ε})
      if len(toks) > 0:
        r = r.union(toks)
      if self.ε not in self.first[m]:
        break
    return r
  
  def _ntrules( self, n ):
    return [rule for rule in self.normalized() if str(rule.nonterminal) == str(n)]
  
  def _compute_parse_table( self ):
    terminals = self._strip_abstract_terminals( self.terminals.copy() )
    NT  = {n.id: n for n in self.nonterminals.values()}
    T   = {t.id: t for t in terminals.values()}
    tab = []
    for N in self._sort_dict(NT):
      rules = []
      for t in self._sort_dict(T):
        next = None
        for R in self._ntrules(N):
          Fip = self._pfirst(R.production)
          if t in Fip or (self.ε in Fip and t in self.follow[N]):
            next = R
            break
        rules.append(next)
      tab.append(rules)
    return tab
  
  def _compute_conflicts( self ):
    for s,N in self.nonterminals.items():
      if self.ε in self.first[N] and len(self.first[N].intersection(self.follow[N])):
        self.conflicts.append( FirstFollowConflict( N, self.first[N], self.follow[N] ) )

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
        if self.first[macro.nonterminal].intersection(self.follow[macro]) != set():
          self.conflicts.append( ListFirstFollowConflict(macro, self.first[macro.nonterminal], self.follow[macro]) )
    return self.conflicts
  
  def _compute_expr_conflicts( self ):
    nud = {}
    led = {}
    morphemes = set(self.terminals.values()).union(set(self.nonterminals.values()))
    for m in morphemes:
      nud[m] = []
      led[m] = []
    for e in self.exprRules:
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
        if e.root == 1: # TODO: root can only be idx 0 or 1, fix that later!
          led[b[0]].append(ExprRule(self._r2d2(b), b, e))
    
    self.nud = {}
    self.led = {}
    for t, r in nud.items():
      u = self._unique(r, lambda x, y: (x.type==y.type and x.type=='symbol'))
      if len(u) > 0:
        self.nud[t] = u[0]

    for t, r in led.items():
      u = self._unique(r, lambda x, y: (x.type==y.type and x.type=='symbol'))
      if len(u) > 0:
        self.led[t] = u[0]

    for terminal, rules in nud.items():
      rules = self._unique(rules, lambda x, y: (x.type==y.type and x.type=='symbol'))
      # TODO: use with --debug
      #if len(rules):
      #  print('nud', terminal, ', '.join([str(x) for x in rules]))
      if len(rules) > 1:
        self.conflicts.append(NudConflict(terminal, [r.rule for r in rules]))
    for terminal, rules in led.items():
      rules = self._unique(rules, lambda x, y: (x.type==y.type and x.type=='symbol'))
      # TODO: use with --debug 
      #if len(rules):
      #  print('led', terminal, ', '.join([str(x) for x in rules]))
      if len(rules) > 1:
        self.conflicts.append(LedConflict(terminal, [r.rule for r in rules]))
  
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
  
  def _sort_dict(self, a):
    return [a[key] for key in sorted(a.keys())]
  
  def _strip_abstract_terminals( self, terminals ):
    for k in ['λ', 'ε', 'σ']:
      if k in terminals:
        del terminals[k]
    return terminals
  

  # Getters / Setters
  def setGrammar( self, nonterminals, terminals, macros, rules, start, exprRules, exprPrecedence ):
    self.nonterminals = nonterminals
    self.terminals = terminals
    self.macros = macros
    self.rules = rules
    self.start = start
    self.conflicts = []
    self.exprRules = exprRules
    self.exprPrecedence = exprPrecedence
    self._compute_first()
    self._compute_follow()
    self._compute_conflicts()
    self._compute_expr_conflicts()
  
  # Query methods
  def isSimpleTerminal( self, t ):
    return isinstance(t, Terminal)
  
  def isSpecialTerminal( self, t ):
    return isinstance(t, Expression) or isinstance(t, EmptyString) or isinstance(t, EndOfStream)
  
  def isTerminal( self, t ):
    return self.isSimpleTerminal(t) or self.isSpecialTerminal(t)
  
  def isNonTerminal( self, n ):
    return type(n) is NonTerminal
  
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
  
  # TODO: remove _getAtomVarName
  def _getAtomVarName( self, atom ):
    if isinstance(atom, Terminal):
      return "TERMINAL_" + str(atom).strip("'").upper()
    if isinstance(atom, NonTerminal):
      return "NONTERMINAL_" + str(atom).upper()
  
  def normalized(self):
    rules = dict()
    for expanded in map(lambda x: x.expand(), self.rules):
      for e in expanded:
        rules[e.id] = e
    return rules.values()
  
  def __str__( self, normalize = True ):
    if normalize:
      rules = self.normalized()
    else:
      rules = self.rules
    return "\n".join([ str(r) for r in rules ])
  
  