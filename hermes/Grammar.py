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
    if name == 'is_empty':
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
  def __init__(self, nonterminal, nudProduction, ledProduction, nudAst, ast, operator, id=0):
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

class Regex:
  def __init__(self, regex, options, terminal, function=None):
    self.__dict__.update(locals())

class Lexer(dict):
  code = ''
  def str(self, theme=None):
    return ', '.join(self.keys())

class CompositeGrammar:
  _empty = EmptyString(-1)
  _end = EndOfStream(-1)

  def __init__(self, name, rules, lexer=Lexer()):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
    self.__dict__.update(locals())
    self.start = None
    self.terminals = set()
    self.nonterminals = set()
    self.macros = set()
    self.expression_terminals = dict()
    self.expression_nonterminals = set()
    self.expanded_rules = list()

    expanded_rules = OrderedDict()
    for rule in rules.copy():
      self.nonterminals.add(rule.nonterminal)
      if self.start is None:
        self.start = rule.nonterminal
      if isinstance(rule, ExprRule):
        expression_terminal = Terminal(rule.nonterminal.string.lower())
        self.expression_nonterminals.add(rule.nonterminal)
        self.expression_terminals[rule.nonterminal] = expression_terminal
        self.terminals.add(expression_terminal)
      for expanded_rule in rule.expand():
        if expanded_rule not in self.expanded_rules:
          self.expanded_rules.append(expanded_rule)
          for morpheme in expanded_rule.production.morphemes:
            if isinstance(morpheme, Terminal):
              self.terminals.add(morpheme)
            elif isinstance(morpheme, NonTerminal):
              self.nonterminals.add(morpheme)
              if morpheme.macro:
                self.macros.add(morpheme.macro)

    self.first_sets = None
    self.follow_sets = None
    progress = True

    # Calculate first/follow sets
    while progress:
      self.first_sets, first_set_changed = self._compute_first(self.first_sets)
      self.follow_sets, follow_set_changed = self._compute_follow(self.first_sets, self.follow_sets)
      progress = first_set_changed | follow_set_changed

    self._compute_conflicts()

    for conflict in self.conflicts:
      if isinstance(conflict, FirstFirstConflict):
        conflict.grammar = self

    nonterminal_rules = {str(n): list() for n in self.nonterminals}
    for rule in self.expanded_rules:
      for morpheme in rule.morphemes:
        if isinstance(morpheme, NonTerminal):
          nonterminal_rules[str(morpheme)].append(rule)

    for nonterminal in self.nonterminals:
      if not len(nonterminal_rules[str(nonterminal)]) and not nonterminal.generated and nonterminal is not self.start:
        self.warnings.append(UnusedNonterminalWarning(nonterminal))

      nRules = self.get_expanded_rules( nonterminal )
      if len(nRules) == 0 and nonterminal is not grammar.start and nonterminal not in [x.nonterminal for x in exprgrammars]:
        self.conflicts.append( UndefinedNonterminalConflict(nonterminal) )
    self._assignIds()

  def __getattr__(self, name):
    if name == 'll1_nonterminals':
      return [x for x in self.nonterminals if x not in [n for n in self.expression_nonterminals]]
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
            Fip = self.first(rule.production)
            if terminal in Fip or (self._empty in Fip and terminal in self.follow(nonterminal)):
              next = rule
              break
          rules.append(next)
        table.append(rules)
      self.__dict__['parse_table'] = table
      return table
    else:
      return self.__dict__[name]

  def first(self, element):
    if isinstance(element, Production):
      first_set = set()
      add_empty_token = True
      for morpheme in element.morphemes:
        if isinstance(morpheme, MorphemeListMacro) or isinstance(morpheme, SeparatedListMacro):
          morpheme = morpheme.start_nt
        morpheme_first_set = set([morpheme]) if isinstance(morpheme, Terminal) else self.first_sets[morpheme]
        toks = morpheme_first_set.difference({self._empty})
        if len(toks) > 0:
          first_set = first_set.union(toks)
        if self._empty not in morpheme_first_set:
          add_empty_token = False
          break
      if add_empty_token:
        first_set.add(self._empty)
      return first_set
    elif isinstance(element, Terminal):
      return {element}
    elif isinstance(element, NonTerminal):
      return self.first_sets[element]

  def follow(self, element):
    if isinstance(element, NonTerminal):
      return self.follow_sets[element]

  def must_consume_tokens(self, nonterminal):
    answer = True
    for rule in self.get_expanded_rules(nonterminal):
      if rule.is_empty:
        answer = False
    return answer

  def getRuleFromFirstSet(self, nonterminal, first):
    rules = self.get_expanded_rules(nonterminal)
    for rule in rules:
      if self.first(rule.production).issuperset(first):
        return rule
    return None

  def _compute_first(self, first=None):
    if first is None:
      first = {nt: set() for nt in self.nonterminals}
    for nt, t in self.expression_terminals.items():
      first[nt].add(t)
    changed = False
    progress = True
    while progress == True:
      progress = False
      for rule in self.expanded_rules:
        try:
          morpheme = rule.production.morphemes[0]
        except IndexError:
          continue

        # TODO: filter out extraneous _empty's in grammar files (e.g. x := _empty + 'a' + _empty)
        if (isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString)) and morpheme not in first[rule.nonterminal]:
          progress = changed = True
          first[rule.nonterminal] = first[rule.nonterminal].union({morpheme})

        elif isinstance(morpheme, NonTerminal):
          add_empty_token = True
          for morpheme in rule.production.morphemes:

            if isinstance(morpheme, NonTerminal):
              sub = first[morpheme]
            elif isinstance(morpheme, Terminal):
              sub = {morpheme}
            else:
              raise Exception('Error: expected either terminal or nonterminal, got ' + morpheme)
            if not first[rule.nonterminal].issuperset(sub.difference({self._empty})):
              progress = changed = True
              first[rule.nonterminal] = first[rule.nonterminal].union(sub.difference({self._empty}))
            if self._empty not in sub:
              add_empty_token = False
              break
          if add_empty_token:
            first[rule.nonterminal] = first[rule.nonterminal].union({self._empty})
    return (first, changed)

  def _compute_follow(self, first, follow=None):
    if follow is None:
      follow = {nt: set() for nt in self.nonterminals}
      follow[self.start] = {self._end}
    changed = False
    progress = True
    while progress == True:
      progress = False

      for rule in self.expanded_rules:
        for index, morpheme in enumerate(rule.production.morphemes):

          if isinstance(morpheme, Terminal) or isinstance(morpheme, EmptyString):
            continue

          try:
            next_morpheme = rule.production.morphemes[index + 1]
          except IndexError:
            next_morpheme = None

          if next_morpheme:
            next_first_set = set([next_morpheme]) if isinstance(next_morpheme, Terminal) else first[next_morpheme].difference({self._empty})
            if not follow[morpheme].issuperset(next_first_set):
              progress = changed = True
              follow[morpheme].update(next_first_set)

          if not next_morpheme or self._empty in self.first(Production(rule.production.morphemes[index+1:])):
            rule_follow_set = follow[rule.nonterminal]
            morpheme_follow_set = follow[morpheme]

            if not morpheme_follow_set.issuperset(rule_follow_set):
              progress = changed = True
              follow[morpheme] = morpheme_follow_set.union(rule_follow_set)
    return (follow, changed)

  def _compute_conflicts(self):
    self.conflicts = []
    self.warnings = []
    nud = {}
    led = {}

    nonterminal_rules = {n: list() for n in self.nonterminals}
    for rule in self.expanded_rules:
      for morpheme in rule.morphemes:
        if isinstance(morpheme, NonTerminal):
          nonterminal_rules[morpheme].append(rule)
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

    for N in self.nonterminals:
      if self._empty in self.first(N) and len(self.first(N).intersection(self.follow(N))):
        self.conflicts.append( FirstFollowConflict(N, self.first(N), self.follow(N)) )

      if len(nonterminal_rules[N]) == 0 and N != self.start:
        self.warnings.append(UnusedNonterminalWarning(N))

      NR = self.get_expanded_rules(N)
      if len(NR) == 0:
        self.conflicts.append(UndefinedNonterminalConflict(N))

      if N not in self.expression_nonterminals:
        for x in NR:
          for y in NR:
            if x == y:
              continue

            x_first = self.first(x.production)
            y_first = self.first(y.production).difference({self._empty})
            intersection = x_first.intersection(y_first)
            if len(intersection) != 0:
              self.conflicts.append(FirstFirstConflict(x, y, self))
    return self.conflicts

  def _assignIds(self):
    morphemes = {}
    i = 0
    for terminal in self.terminals:
      if not isinstance(terminal, AbstractTerminal):
        terminal.id = i
        morphemes[str(terminal)] = terminal.id
        i += 1
    for nonterminal in self.nonterminals:
      nonterminal.id = i
      morphemes[str(nonterminal)] = nonterminal.id
      i += 1

    for rule_set in [self.rules, self.expanded_rules]:
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

  def get_expanded_rules(self, nonterminal=None):
    if nonterminal:
      return [rule for rule in self.expanded_rules if str(rule.nonterminal) == str(nonterminal)]
    return self.expanded_rules

  def get_rules(self, nonterminal=None):
    if nonterminal:
      return [rule for rule in self.rules if str(rule.nonterminal) == str(nonterminal)]
    return self.expanded_rules

  def ruleFirst(self, rule):
    if isinstance(rule, ExprRule):
      if len(rule.nudProduction) and rule.nudProduction.morphemes[0] != rule.nonterminal:
        return self._pfirst(rule.nudProduction)
    return self._pfirst(rule.production)

  def getExpressionTerminal(self):
    # TODO: this needs to be fixed.
    return self.expression_terminals

  def getExpandedLL1Rules(self, nonterminal = None):
    all_rules = [rule for rule in self.expanded_rules if isinstance(rule, Rule)]
    if nonterminal:
      return [rule for rule in all_rules if str(rule.nonterminal) == str(nonterminal)]
    return all_rules

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
