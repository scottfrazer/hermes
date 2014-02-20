import re, json
from collections import OrderedDict
from hermes.Morpheme import NonTerminal, Terminal, EmptyString
from hermes.Grammar import CompositeGrammar, LL1GrammarFactory, ExpressionGrammarFactory, Lexer, Regex
from hermes.Grammar import Rule, ExprRule, MacroGeneratedRule, Production, AstSpecification, AstTranslation
from hermes.Grammar import InfixOperator, PrefixOperator, MixfixOperator, OperatorPrecedence
from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro
from hermes.Logger import Factory as LoggerFactory

from hermes.parser.hermes.Lexer import Terminal as HermesTerminal
from hermes.parser.Common import Ast, AstList, AstPrettyPrintable

logger = LoggerFactory().getModuleLogger(__name__)

class GrammarFactoryNew:
  # TODO: I want to get rid of name and start parameters
  def create(self, name, ast):
    self.next_id = 0
    self.binding_power = 0

    terminals = {
      '_empty': EmptyString(-1)
    }
    for terminal in self.walk_ast_terminal(ast, 'terminal'):
      t_name = terminal.source_string
      if t_name not in terminals:
        terminals[t_name] = Terminal(t_name, len(terminals))

    nonterminals = {}
    for nonterminal in self.walk_ast_terminal(ast, 'nonterminal', stop=True):
      nt_name = nonterminal.source_string
      if nt_name not in nonterminals:
        nonterminals[nt_name] = NonTerminal(nt_name, len(nonterminals))

    lexer = None
    lexer_ast = self.walk_ast(ast, 'Lexer')
    if len(lexer_ast) > 1:
      raise Exception('Expecting only one lexer')
    elif len(lexer_ast) == 1:
      lexer_ast = lexer_ast[0]
      lexer = self.parse_lexer(lexer_ast, terminals, nonterminals)
      lexer.code = ast.getAttr('code').source_string

    macros = {}
    for macro in self.walk_ast(ast, 'Macro'):
      macro_string = self.macro_ast_to_string(macro)
      if macro_string in macros:
        continue
      if macro.getAttr('name').source_string == 'list' and len(macro.getAttr('parameters')) == 2:
        macro = self.slist(macro, terminals, nonterminals)
      elif macro.getAttr('name').source_string == 'list' and len(macro.getAttr('parameters')) == 1:
        macro = self.nlist(macro, terminals, nonterminals)
      elif macro.getAttr('name').source_string == 'tlist':
        macro = self.slist(macro, terminals, nonterminals)
      elif macro.getAttr('name').source_string == 'mlist':
        macro = self.mlist(macro, terminals, nonterminals)
      elif macro.getAttr('name').source_string == 'optional':
        macro = self.optional(macro, terminals, nonterminals)
      macros[macro_string] = macro

    expression_parser_asts = []
    ll1_rules = []
    start = None
    for rule_ast in self.walk_ast(ast, 'Rule'):
      if start is None:
        start = self.get_morpheme_from_lexer_token(rule_ast.getAttr('nonterminal'), terminals, nonterminals)
      production_ast = rule_ast.getAttr('production')
      if isinstance(production_ast, Ast) and production_ast.name == 'ExpressionParser':
        expression_parser_asts.append(rule_ast)
      else:
        new_rules = self.parse_ll1_rule(rule_ast, terminals, nonterminals, macros)
        ll1_rules.extend(new_rules) # Bill Maher!

    expression_grammars = []
    for expression_parser_ast in expression_parser_asts:
      nonterminal = self.get_morpheme_from_lexer_token(expression_parser_ast.getAttr('nonterminal'), terminals, nonterminals)
      expression_rules = []
      precedence = {}
      for expression_rule_ast in expression_parser_ast.getAttr('production').getAttr('rules'):
        rules = self.parse_expr_rule(expression_rule_ast, nonterminal, terminals, nonterminals, macros)
        expression_rules.extend(rules)
      grammar = ExpressionGrammarFactory().create(
        set(nonterminals.values()),
        set(terminals.values()),
        macros.values(),
        expression_rules,
        precedence,
        nonterminal
      )
      expression_grammars.append(grammar)

    ll1_grammar = LL1GrammarFactory().create(
      name,
      set(nonterminals.values()),
      set(terminals.values()),
      macros.values(),
      set(ll1_rules),
      start 
    )

    return CompositeGrammar(name, ll1_grammar, expression_grammars, lexer)

  def parse_lexer(self, lexer_ast, terminals, nonterminals):
    lexer = Lexer()
    for lexer_atom in lexer_ast.getAttr('atoms'):
      if lexer_atom.name == 'Regex':
        regex = self.parse_regex(lexer_atom, terminals, nonterminals)
        if 'default' not in lexer: lexer['default'] = []
        lexer['default'].append(regex)
      if lexer_atom.name == 'Mode':
        mode_name = lexer_atom.getAttr('name').source_string
        lexer[mode_name] = self.parse_lexer_mode(lexer_atom, terminals, nonterminals)
    return lexer
        
  def parse_regex(self, regex_ast, terminals, nonterminals):
    (terminal, options, function) = (None, [], None)
    onmatch = regex_ast.getAttr('onmatch')
    if isinstance(onmatch, HermesTerminal):
      terminal = self.get_morpheme_from_lexer_token(onmatch, terminals, nonterminals)
    elif onmatch.name == 'LexerFunctionCall':
      if onmatch.getAttr('terminal') is not None:
        terminal = self.get_morpheme_from_lexer_token(onmatch.getAttr('terminal'), terminals, nonterminals)
      function = onmatch.getAttr('name').source_string
    elif onmatch.name == 'Null':
      terminal = None
   
    if regex_ast.getAttr('options') is not None:
      for option in regex_ast.getAttr('options'):
        options.append(option.source_string)

    return Regex(
        regex_ast.getAttr('regex').source_string,
        options,
        terminal,
        function
    )

  def parse_lexer_mode(self, mode_ast, terminals, nonterminals):
    regex_list = []
    for ast in mode_ast.getAttr('atoms'):
      if ast.name == 'Regex':
        regex_list.append(self.parse_regex(ast, terminals, nonterminals))
    return regex_list

  def parse_expr_rule(self, rule_ast, expr_nonterminal, terminals, nonterminals, macros):
    rules = []
    operator = None

    nonterminal = self.get_morpheme_from_lexer_token(rule_ast.getAttr('nonterminal'), terminals, nonterminals)
    production = rule_ast.getAttr('production')
    precedence = rule_ast.getAttr('precedence')

    associativity = None
    if precedence is not None:
      if precedence.getAttr('marker').str == 'asterisk':
        self.binding_power += 1000
      associativity = precedence.getAttr('associativity').source_string
   
    if nonterminal != expr_nonterminal:
      raise Exception('parse_expr_rule(): Expecting rule nonterminal to match parser nonterminal')

    if production.name == 'InfixProduction':
      morphemes = production.getAttr('morphemes')
      ast = production.getAttr('ast')

      if len(morphemes) != 3:
        raise Exception('parse_expr_rule(): InfixProduction needs 3 morphemes')

      first = self.get_morpheme_from_lexer_token(morphemes[0], terminals, nonterminals)
      operator = self.get_morpheme_from_lexer_token(morphemes[1], terminals, nonterminals)
      third = self.get_morpheme_from_lexer_token(morphemes[2], terminals, nonterminals)

      if not (first == third == expr_nonterminal):
        raise Exception("parse_expr_rule(): first == third == expr_nonterminal")
      if not isinstance(operator, Terminal):
        raise Exception("parse_expr_rule(): operator needs to be a terminal")

      rules.append(ExprRule(
        expr_nonterminal,
        Production([expr_nonterminal]),
        Production([operator, expr_nonterminal]),
        AstTranslation(0),
        self.parse_ast(ast),
        InfixOperator(operator, self.binding_power, associativity)
      ))

    elif production.name == 'MixfixProduction':
      nud_morphemes_ast = production.getAttr('nud')
      led_morphemes_ast = production.getAttr('led')
      led_ast = production.getAttr('ast')
      nud_ast = production.getAttr('nud_ast')

      nud_morphemes = []
      if nud_morphemes_ast:
        for nud_morpheme in nud_morphemes_ast:
          if isinstance(nud_morpheme, Ast) and nud_morpheme.name == 'Macro':
            macro = macros[self.macro_ast_to_string(nud_morpheme)]
            nud_morphemes.append(macro.start_nt)
          else:
            nud_morphemes.append(self.get_morpheme_from_lexer_token(nud_morpheme, terminals, nonterminals))

      led_morphemes = []
      if led_morphemes_ast:
        for led_morpheme in led_morphemes_ast:
          if isinstance(led_morpheme, Ast) and led_morpheme.name == 'Macro':
            macro = macros[self.macro_ast_to_string(led_morpheme)]
            led_morphemes.append(macro.start_nt)
          else:
            led_morphemes.append(self.get_morpheme_from_lexer_token(led_morpheme, terminals, nonterminals))

      operator = None
      if len(led_morphemes):
        operator = MixfixOperator(led_morphemes[0], self.binding_power, associativity)

      rules.append(ExprRule(
        expr_nonterminal,
        Production(nud_morphemes),
        Production(led_morphemes),
        self.parse_ast(nud_ast),
        self.parse_ast(led_ast) if led_ast else None,
        operator
      ))

    elif production.name == 'PrefixProduction':
      morphemes = production.getAttr('morphemes')
      ast = production.getAttr('ast')

      if len(morphemes) != 2:
        raise Exception('parse_expr_rule(): InfixProduction needs 2 morphemes')

      operator = self.get_morpheme_from_lexer_token(morphemes[0], terminals, nonterminals)
      operand = self.get_morpheme_from_lexer_token(morphemes[1], terminals, nonterminals)

      if not operand == expr_nonterminal:
        raise Exception("parse_expr_rule(): operand == expr_nonterminal")
      if not isinstance(operator, Terminal):
        raise Exception("parse_expr_rule(): operator needs to be a terminal")

      rules.append(ExprRule(
        expr_nonterminal,
        Production([operator, expr_nonterminal]),
        Production(),
        AstTranslation(0),
        self.parse_ast(ast),
        PrefixOperator(operator, self.binding_power, associativity)
      ))

    else:
      raise Exception("Improperly formatted rule")

    return rules

  def parse_ll1_rule(self, rule_ast, terminals, nonterminals, macros):
    nonterminal = self.get_morpheme_from_lexer_token(rule_ast.getAttr('nonterminal'), terminals, nonterminals)
    production_list_ast = rule_ast.getAttr('production')

    rules = []
    for production_ast in production_list_ast:
      morphemes_list_ast = production_ast.getAttr('morphemes')
      ast_ast = production_ast.getAttr('ast')
      morphemes = []
      for morpheme_ast in morphemes_list_ast:
        if isinstance(morpheme_ast, HermesTerminal):
          morpheme = self.get_morpheme_from_lexer_token(morpheme_ast, terminals, nonterminals)
        elif isinstance(morpheme_ast, Ast) and morpheme_ast.name == 'Macro':
          morpheme = macros[self.macro_ast_to_string(morpheme_ast)]
        else:
          raise Exception('Unknown AST element: ' + morpheme_ast)
        morphemes.append(morpheme)
      ast = self.parse_ast(ast_ast)
      rules.append( Rule(nonterminal, Production(morphemes), id=0, root=0, ast=ast) )
    return rules
  
  def parse_ast(self, ast_ast):
    if ast_ast is None:
      return AstTranslation(0)
    elif isinstance(ast_ast, Ast) and ast_ast.name == 'AstTransformation':
      node_name = ast_ast.getAttr('name').source_string
      parameters = OrderedDict()
      for parameter_ast in ast_ast.getAttr('parameters'):
        name = parameter_ast.getAttr('name').source_string
        index = parameter_ast.getAttr('index').source_string
        parameters[name] = index
      return AstSpecification(node_name, parameters)
    elif isinstance(ast_ast, HermesTerminal) and ast_ast.str == 'nonterminal_reference':
      return AstTranslation(int(ast_ast.source_string))
    else:
      raise Exception('parse_ast(): invalid AST: ' + ast_ast)

  def macro_ast_to_string(self, ast):
    return '{}({})'.format(ast.getAttr('name').source_string, ','.join([self.morpheme_to_string(x) for x in ast.getAttr('parameters')]))

  def morpheme_to_string(self, morpheme):
    return ':' + morpheme.source_string if morpheme.str == 'terminal' else '$' + morpheme.source_string

  def get_morpheme_from_lexer_token(self, token, terminals, nonterminals):
    if token.str == 'nonterminal':
      return nonterminals[token.source_string]
    if token.str == 'terminal':
      return terminals[token.source_string]

  def generate_nonterminal(self, nonterminals):
    name = '_gen' + str(self.next_id)
    self.next_id += 1
    nt = NonTerminal(name, len(nonterminals), generated=True)
    nonterminals[nt.string] = nt
    return nt

  def mlist( self, ast, terminals, nonterminals ):
    morpheme = self.get_morpheme_from_lexer_token(ast.getAttr('parameters')[0], terminals, nonterminals)
    minimum = int(ast.getAttr('parameters')[1].source_string)
    nt0 = self.generate_nonterminal(nonterminals)
    nt1 = self.generate_nonterminal(nonterminals)
    empty = terminals['_empty']

    prod = [morpheme for x in range(minimum)]
    prod.append(nt1)
    rules = [
      MacroGeneratedRule(nt0, Production( prod )),
      MacroGeneratedRule(nt1, Production( [morpheme, nt1] )),
      MacroGeneratedRule(nt1, Production( [empty] ))
    ]
    if minimum == 0:
      rules.append( MacroGeneratedRule(nt0, Production( [empty] )) )

    macro = MinimumListMacro(morpheme, minimum, nt0, rules)

    for rule in rules:
      rule.nonterminal.macro = macro

    return macro

  def optional( self, ast, terminals, nonterminals ):
    morpheme = self.get_morpheme_from_lexer_token(ast.getAttr('parameters')[0], terminals, nonterminals)
    nt0 = self.generate_nonterminal(nonterminals)
    empty = terminals['_empty']
    rules = [
      MacroGeneratedRule(nt0, Production( [morpheme] )),
      MacroGeneratedRule(nt0, Production( [empty] ))
    ]

    macro = OptionalMacro(morpheme, nt0, rules)

    for rule in rules:
      rule.nonterminal.macro = macro

    return macro

  def nlist( self, ast, terminals, nonterminals ):
    morpheme = self.get_morpheme_from_lexer_token(ast.getAttr('parameters')[0], terminals, nonterminals)
    nt0 = self.generate_nonterminal(nonterminals)
    empty = terminals['_empty']

    rules = [
      MacroGeneratedRule(nt0, Production( [morpheme, nt0] )),
      MacroGeneratedRule(nt0, Production( [empty] ))
    ]

    macro = MorphemeListMacro(morpheme, nt0, rules)

    for rule in rules:
      rule.nonterminal.macro = macro

    return macro

  def slist( self, ast, terminals, nonterminals ):
    empty = terminals['_empty']
    morpheme = self.get_morpheme_from_lexer_token(ast.getAttr('parameters')[0], terminals, nonterminals)
    separator = self.get_morpheme_from_lexer_token(ast.getAttr('parameters')[1], terminals, nonterminals)
    separator.isSeparator = True

    minimum = 0
    if len(ast.getAttr('parameters')) == 3:
       minimum = int(ast.getAttr('parameters')[2].source_string)

    nt0 = self.generate_nonterminal(nonterminals)
    nt1 = self.generate_nonterminal(nonterminals)

    if minimum > 0:
      items = [morpheme] * (2*minimum-1)
      for x in filter(lambda x: x % 2 == 1, range(2 * minimum - 1)): # all odd numbers in range
        items[x] = separator
      items.append(nt1)
    else:
      items = [morpheme, nt1]

    rules = [
        MacroGeneratedRule(nt0, Production( items )),
        MacroGeneratedRule(nt1, Production( [separator, morpheme, nt1] )),
        MacroGeneratedRule(nt1, Production( [empty] ))
    ]

    if minimum == 0:
      rules.append( MacroGeneratedRule(nt0, Production( [empty] )) )

    macro = SeparatedListMacro(morpheme, separator, nt0, rules)

    for rule in rules:
      rule.nonterminal.macro = macro

    return macro

  def tlist( self, ast, terminals, nonterminals ):
    nt0 = self.generate_nonterminal(nonterminals)
    empty = terminals['_empty']
    morpheme = terminals[ast.getAttr('parameters')[0].source_string]
    terminator = terminals[ast.getAttr('parameters')[1].source_string]
    rules = [
        MacroGeneratedRule(nt0, Production( [morpheme, terminator, nt0] )),
        MacroGeneratedRule(nt0, Production( [empty] ))
    ]

    macro = TerminatedListMacro(morpheme, terminator, nt0, rules)

    for rule in rules:
      rule.nonterminal.macro = macro

    return macro 

  def walk_ast_terminal(self, ast, terminal, stop=False):
    nodes = []
    if isinstance(ast, HermesTerminal) and ast.str == terminal:
      return [ast]
    if not isinstance(ast, Ast): return nodes
    for key, sub in ast.attributes.items():
      if isinstance(sub, HermesTerminal) and sub.str == terminal:
        nodes.append(sub)
      elif isinstance(sub, Ast):
        nodes.extend(self.walk_ast_terminal(sub, terminal))
      elif isinstance(sub, AstList):
        for ast1 in sub:
          nodes.extend(self.walk_ast_terminal(ast1, terminal))
    return nodes

  def walk_ast(self, ast, node_name):
    nodes = []
    if not isinstance(ast, Ast): return nodes
    if ast.name == node_name: nodes.append(ast)
    for key, sub in ast.attributes.items():
      if isinstance(sub, Ast):
        nodes.extend(self.walk_ast(sub, node_name))
      elif isinstance(sub, AstList):
        for ast in sub:
          nodes.extend(self.walk_ast(ast, node_name))
    return nodes

class GrammarParser:
  def get_ast(self, name, fp):
    from hermes.parser.hermes import lex, parse
    tree = parse(lex(fp))
    return tree.toAst()

  def parse(self, name, fp):
    ast = self.get_ast(name, fp)
    return GrammarFactoryNew().create(name, ast)
