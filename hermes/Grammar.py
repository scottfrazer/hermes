from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Expression
from hermes.Morpheme import Morpheme
from hermes.Conflict import FirstFirstConflict
from hermes.Conflict import FirstFollowConflict, ListFirstFollowConflict
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

class Grammar:

  # Special Terminals
  ε = EmptyString(0)
  λ = Expression(1)
  σ = EndOfStream(2)

  # Internal
  def _compute_first( self ):
    self.first = dict()
    for s,N in self.nonterminals.items():
      if s.upper() == 'EXPR':
        self.first[N] = {self.λ}
      else:
        self.first[N] = set()
    for s,N in self.terminals.items():
      self.first[N] = {N}
    for M in self.macros:
      if isinstance(M, NonterminalListMacro) or isinstance(M, SeparatedListMacro):
        if str(M.start_nt).upper() == 'EXPR':
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

        elif type(morpheme) is NonTerminal and morpheme.string.upper() == 'EXPR' and self.λ not in self.first[R.nonterminal]:
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
    return [rule for rule in self.rules if str(rule.nonterminal) == str(n)]
  
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
    self.conflicts = []
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
  # Getters/Setters: setGrammar, setExprGrammar, getTerminals, getNonterminals, getRules, getStart
  
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
    self.exprRules = exprRules
    self.exprPrecedence = exprPrecedence
    self._compute_first()
    self._compute_follow()
    self._compute_conflicts()
  
  # Query methods
  def isSimpleTerminal( self, t ):
    return isinstance(t, Terminal)
  
  def isSpecialTerminal( self, t ):
    return isinstance(t, Expression) or isinstance(t, EmptyString) or isinstance(t, EndOfStream)
  
  def isTerminal( self, t ):
    return self.isSimpleTerminal(t) or self.isSpecialTerminal(t)
  
  def isNonTerminal( self, n ):
    return type(n) is NonTerminal
  

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
  
  