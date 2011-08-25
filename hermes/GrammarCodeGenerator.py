from os import path
import re
from pkg_resources import resource_filename
from types import *
from hermes.Morpheme import Terminal, NonTerminal, EmptyString
from hermes.Macro import ExprListMacro, NonterminalListMacro, SeparatedListMacro
from hermes.Grammar import MacroGeneratedRule, AstSpecification, AstTranslation
from hermes.Logger import Factory as LoggerFactory
import moody

moduleLogger = LoggerFactory().getModuleLogger(__name__)

class Template:
  pass

class PythonTemplate(Template):
  template = 'parser.tpl'
  destination = 'Parser.py'
  def __init__(self, resources):
    self.resources = resources
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  def render(self):
    x = { 
      'tokens': self.resources.getTokens(),
      'rules': self.resources.getRules(),
      'expr_rules': self.resources.getExprGrammars(),
      'entry': self.resources.getEntry(),
      'entry_points': self.resources.getEntryPoints(),
      'parser': self.resources.getParser(),
      'init': self.resources.getDeclarations(),
      'nudled': self.resources.getNudLed(),
      'add_main': self.resources.add_main
    }
    templates_dir = resource_filename(__name__, 'templates')
    loader = moody.make_loader(templates_dir)
    code = loader.render( self.template, add_main=x['add_main'], rules=x['rules'], expr_rules=x['expr_rules'], tokens=x['tokens'], entry=x['entry'], nt=x['parser'], init=x['init'], entry_points=x['entry_points'], nudled=x['nudled'])
    linereduce = re.compile('^[ \t]*$', re.M)
    code = linereduce.sub('', code)
    code = re.sub('\n+', '\n', code)
    return code

class CSourceTemplate(Template):
  template = 'c/header.tpl'
  destination = 'parser.h'
  def __init__(self, resources):
    self.resources = resources
  def render(self):
    raise Exception('Not Implemented')
  
class CHeaderTemplate(Template):
  template = 'c/source.tpl'
  destination = 'parser.c'
  def __init__(self, resources):
    self.resources = resources
  def render(self):
    raise Exception('Not Implemented')
  
class Resources:
  def __init__(self, grammar, tokens = [], add_main = False):
    self.grammar = grammar
    self.add_main = add_main
    self.tokens = tokens
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  def getbp( self, terminal, grammar, assoc = ['left', 'right']):
    precedence = grammar.getPrecedence()
    if terminal not in precedence:
      return 0
    for p in precedence[terminal]:
      if p.associativity.lower() == 'left' and 'left' in assoc:
        return p.precedence
      if p.associativity.lower() == 'right' and 'right' in assoc:
        return p.precedence - 1
      if p.associativity.lower() == 'unary' and 'unary' in assoc:
        return p.precedence
    return 0
  
  def ruletotpl( self, grammar, expr_rule ):
    rule = expr_rule.rule
    atoms = rule.production.morphemes[rule.root:]
    tpl = []
    if expr_rule.type == 'infix':
      tpl.append({
        'type': 'infix',
        'binding_power': self.getbp(atoms[1], grammar),
        'rule': rule
      })
    elif expr_rule.type == 'prefix':
      tpl.append({
        'type': 'prefix',
        'binding_power': self.getbp(atoms[0], grammar, ['unary']),
        'rule': rule
      })
    elif expr_rule.type == 'symbol':
      tpl.append({
        'type': 'symbol',
        'sym': rule.production.morphemes[0].id,
        'rule': rule
      })
    elif expr_rule.type == 'mixfix':
      i = 0
      while i < len(atoms):
        atom = atoms[i]
        if isinstance(atom, Terminal):
          # TODO: handling of the expression list macro is sloppy...
          if i < len(atoms) - 2 and isinstance(atoms[i+1], ExprListMacro) and isinstance(atoms[i+2], Terminal):
            tpl.append({
              'type': 'list',
              'open_sym': atoms[i].id,
              'close_sym': atoms[i+2].id,
              'separator': atoms[i+1].separator.id,
              'nonterminal_func': '_' + str(atoms[i+1].nonterminal).upper(),
              'rule': rule
            })
            i += 3
            continue
          else:
            tpl.append({
              'type': 'symbol-append',
              'sym': atom.id,
              'rule': rule
            })
        elif isinstance(atom, NonTerminal):
          tpl.append({
              'type': 'nonterminal',
              'nonterminal_func': '_' + str(atom).upper(),
              'binding_power': self.getbp(atom, grammar),
              'rule': rule
            })
        i += 1
    return tpl
  
  def getEntry(self):
    return str(self.grammar.getLL1Grammar().getStart()).lower()
  
  def getParser(self):
    tab = self.grammar._compute_parse_table()
    tpl = {}
    for N in self.grammar.nonterminals:
      # TODO: change this...
      if str(N).lower() == '_expr':
        continue
      tpl[N.id] = {
        'nt_obj': N,
        'empty': False,
        'lambda_path': False,
        'lambda_path_atoms': [],
        'rules': [],
        'escape_terminals': set(),
        'follow': self.grammar.follow(N).difference(set([self.grammar.ε, self.grammar.σ]))
      }
    for id, tpl_nt in tpl.items():
      N = tpl_nt['nt_obj']
      for rule in self.grammar.getLL1Grammar()._ntrules(N):
        tpl_rule = {
          'obj': rule,
          'atoms': []
        }

        if len(rule.production.morphemes) == 1 and rule.production.morphemes[0] == self.grammar.ε:
          tpl_nt['empty'] = True
          continue

        if self.grammar.λ in self.grammar._pfirst(rule.production):
          tpl_nt['lambda_path'] = rule
          tpl_nt['lambda_path_atoms'] = []
          self.logger.debug("Nonterminal %s leads to λ through %s" %(N, rule))
          for x in rule.production.morphemes:
            tpl_type = tpl_terminal_var_name = tpl_nonterminal_func_name = ''
            if self.grammar.isSimpleTerminal(x):
              atom = x
            elif self.grammar.isNonTerminal(x):
              atom = x
            elif isinstance(x, SeparatedListMacro) or isinstance(x, NonterminalListMacro):
              atom = x.start_nt
            tpl_nt['lambda_path_atoms'].append(atom)
          # if λ path != nonterminal... something went horribly wrong.
          # Also, if λpath is already set, that might be potentially bad.
        for atom in rule.production.morphemes:
          if isinstance(atom, NonterminalListMacro) or isinstance(atom, SeparatedListMacro):
            tpl_rule['atoms'].append(atom.start_nt)
            escape_terminals = set(self.grammar.follow[atom.start_nt].difference({self.grammar.ε, self.grammar.σ, self.grammar.λ}))
            tpl[atom.start_nt.id]['escape_terminals'] = tpl[atom.start_nt.id]['escape_terminals'].union( escape_terminals )
          elif self.grammar.isSimpleTerminal(atom) or self.grammar.isNonTerminal(atom):
            tpl_rule['atoms'].append(atom)
        tpl_nt['rules'].append( tpl_rule )
    return list(tpl.values())
  
  def getNudLed(self):
    templates = []
    for index, grammar in enumerate(self.grammar.getExpressionGrammars()):
      self.precedence = {}
      for terminal, precedence in grammar.getPrecedence().items():
        for p in precedence:
          if p.associativity in ['left', 'right']:
            self.precedence[terminal] = p.precedence

      tpl = {
        'nonterminal': str(grammar.nonterminal),
        'index': index,
        'precedence': {k.id: v for k,v in self.precedence.items()},
        'nud': {},
        'led': {}
      }

      self.logger.debug('Nud/Led definitions for expression grammar nonterminal %s (index %d)' % (tpl['nonterminal'], tpl['index']))
      newPrecedence = dict(map(lambda x: (x, []), set(self.precedence.values())))
      for terminal, precedence in self.precedence.items():
        newPrecedence[precedence].append(terminal)
      self.logger.debug('Operator precedence map:')
      for (precedence, terminals) in sorted(newPrecedence.items(), key=lambda x: x[0]):
        self.logger.debug('%s: %s' % (precedence, ', '.join([str(x) for x in terminals])))

      def debugTemplates(func, templates):
        for template in templates:
          if template['type'] == 'symbol-append':
            self.logger.debug('%s(%s) += (%s, %s, %s)' % (func, terminal, template['type'], template['sym'], template['rule']))
          if template['type'] == 'nonterminal':
            self.logger.debug('%s(%s) += (%s, %s(), %s)' % (func, terminal, template['type'], template['nonterminal_func'], template['rule']))
          if template['type'] == 'prefix':
            self.logger.debug('%s(%s) += (%s, %s)' % (func, terminal, template['type'], template['rule']))
          if template['type'] == 'infix':
            self.logger.debug('%s(%s) += (%s, %s)' % (func, terminal, template['type'], template['rule']))
          if template['type'] == 'list':
            self.logger.debug('%s(%s) += (%s, open=%s, close=%s, func=%s())' % (func, terminal, template['type'], template['open_sym'], template['close_sym'], template['nonterminal_func']))
          if template['type'] == 'symbol':
            self.logger.debug('%s(%s) += (%s, %s)' % (func, terminal, template['type'], template['sym']))

      for terminal, rule in grammar.nud.items():
        temp = self.ruletotpl(grammar, rule)
        debugTemplates('nud', temp)
        tpl['nud'][terminal.id] = temp

      for terminal, rule in grammar.led.items():
        temp = self.ruletotpl(grammar, rule)
        debugTemplates('led', temp)
        tpl['led'][terminal.id] = temp

      templates.append(tpl)
    return templates
  
  def getDeclarations(self):
    tab = self.grammar._compute_parse_table()
    terminals = self.grammar._strip_abstract_terminals( self.grammar.terminals.copy() )

    terminal_str = {}
    terminal_var = {}
    for t in terminals:
      terminal_str[t.id] =  t.string
      terminal_var[t.id] = 'TERMINAL_' + str(t).strip("'").upper()

    nonterminal_str = {}
    nonterminal_var = {}
    for n in self.grammar.nonterminals:
      nonterminal_str[n.id] =  n.string
      nonterminal_var[n.id] = 'NONTERMINAL_' + str(n).upper()

    tpl = {
      'terminal_count': len(terminals),
      'nonterminal_count': len(self.grammar.nonterminals),
      'terminal_start': 0,
      'terminal_end': len(terminals) - 1,
      'nonterminal_start': len(terminals),
      'nonterminal_end': len(terminals) + len(self.grammar.nonterminals) - 1,
      'parse_table': ',\n  '.join(['[' + ', '.join([str(r.id) if r else str(-1) for r in tab[i]]) + ']' for i in range(len(self.grammar.nonterminals))]),
      'terminal_str': terminal_str,
      'nonterminal_str': nonterminal_str,
      'terminal_var': terminal_var,
      'nonterminal_var': nonterminal_var
    }

    return tpl
  
  def getEntryPoints(self):
    return {str(self.grammar.getLL1Grammar().getStart()).lower(): '_'+str(self.grammar.getLL1Grammar().start).upper()}
  
  def getTokens(self):
    return self.tokens
  
  def getRules(self):
    return {r.id: r for r in self.grammar.getNormalizedLL1Rules() if type(r) is not MacroGeneratedRule}
  
  def getExprGrammars(self):
    return self.grammar.getExpressionGrammars()
  

class GrammarCodeGenerator:
  def __init__(self, template, directory):
    self.template = template
    self.directory = directory
  
  def generate( self ):
    #try:
      fp = open( path.join( self.directory, self.template.destination ), 'w' )
      fp.write( self.template.render() )
      fp.close()
      return True
    #except:
    #  return False