from os import path
import re
from pkg_resources import resource_filename
from types import *
from hermes.Morpheme import Terminal, NonTerminal, EmptyString
from hermes.Macro import ExprListMacro, NonterminalListMacro, SeparatedListMacro
from hermes.Grammar import MacroGeneratedRule, AstSpecification, AstTranslation
import moody

class Template:
  pass

class PythonTemplate(Template):
  template = 'parser.tpl'
  destination = 'Parser.py'
  def __init__(self, resources):
    self.resources = resources
  def render(self):
    x = { 
      'tokens': self.resources.getTokens(),
      'rules': self.resources.getRules(),
      'expr_rules': self.resources.getExprRules(),
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

class CHeaderTemplate(Template):
  template = 'c/source.tpl'
  destination = 'parser.c'
  def __init__(self, resources):
    self.resources = resources

class Resources:
  def __init__(self, grammar, tokens = [], add_main = False):
    self.grammar = grammar
    self.add_main = add_main
    self.tokens = tokens

  def getbp( self, terminal, assoc = ['left', 'right']):
    bp = self.grammar.exprPrecedence[terminal]
    for (power, a) in bp:
      if a.lower() == 'left' and 'left' in assoc:
        return power
      if a.lower() == 'right' and 'right' in assoc:
        return power - 1
      if a.lower() == 'unary' and 'unary' in assoc:
        return power
    return -1
  
  def ruletotpl( self, expr_rule ):
    rule = expr_rule.rule
    atoms = rule.production.morphemes[rule.root:]
    tpl = []
    if expr_rule.type == 'infix':
      tpl.append({
        'type': 'infix',
        'binding_power': self.getbp(atoms[1]),
        'rule': rule
      })
    elif expr_rule.type == 'prefix':
      tpl.append({
        'type': 'prefix',
        'binding_power': self.getbp(atoms[0], ['unary']),
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
              'type': 'symbol',
              'sym': atom.id,
              'rule': rule
            })
        elif isinstance(atom, NonTerminal):
          tpl.append({
              'type': 'nonterminal',
              'nonterminal_func': '_' + str(atom).upper(),
              'rule': rule
            })
        i += 1
    return tpl
  
  def getEntry(self):
    return str(self.grammar.start).lower()
  
  def getParser(self):
    tab = self.grammar._compute_parse_table()
    tpl = {}
    for N in self.grammar.nonterminals.values():
      # EXPR is parsed via Pratt Parser
      if str(N) == 'EXPR':
        continue
      tpl[N.id] = {
        'nt_obj': N,
        'func_name': '_' + str(N).upper(),
        'id': N.id,
        'empty': False,
        'lambda_path': False,
        'lambda_path_atoms': '',
        'rules': [],
        'escape_terminals': set(),
        #'follow': self.grammar.follow[N].difference(set([self.grammar.ε, self.grammar.σ, self.grammar.λ]))
        'follow': self.grammar.follow[N].difference(set([self.grammar.ε, self.grammar.σ]))
      }
    for id, tpl_nt in tpl.items():
      N = tpl_nt['nt_obj']
      for i, rule in enumerate( self.grammar._ntrules(N) ):
        tpl_rule = {
          'idx': i,
          'id': rule.id,
          'obj': rule,
          'atoms': []
        }

        if len(rule.production.morphemes) == 1 and rule.production.morphemes[0] == self.grammar.ε:
          tpl_nt['empty'] = True
          continue

        if self.grammar.λ in self.grammar._pfirst(rule.production):
          tpl_nt['lambda_path'] = rule
          tpl_nt['lambda_path_atoms'] = []
          for x in rule.production.morphemes:
            tpl_type = tpl_terminal_var_name = tpl_nonterminal_func_name = ''
            if self.grammar.isSimpleTerminal(x):
              tpl_type = 'terminal'
              tpl_terminal_var_name = self.grammar._getAtomVarName(x)
            elif self.grammar.isNonTerminal(x):
              tpl_type = 'nonterminal'
              tpl_nonterminal_func_name = '_' + str(x).upper()
            elif isinstance(x, SeparatedListMacro) or isinstance(x, NonterminalListMacro):
              tpl_type = 'nonterminal'
              tpl_nonterminal_func_name = '_' + str(x.start_nt).upper()
            tpl_nt['lambda_path_atoms'].append({
              'type': tpl_type,
              'terminal_var_name': tpl_terminal_var_name,
              'nonterminal_func_name': tpl_nonterminal_func_name
            })
          # print("NT %s leads to λ through %s" %(N, rule))
          # if λ path != nonterminal... something went horribly wrong.
          # Also, if λpath is already set, that might be potentially bad.
        for atom in rule.production.morphemes:
          if isinstance(atom, NonterminalListMacro) or isinstance(atom, SeparatedListMacro):
            tpl_rule['atoms'].append({
              'type': 'nonterminal',
              'terminal_var_name': '',
              'nonterminal_func_name': '_' + str(atom.start_nt).upper()
            })
            escape_terminals = set(map(lambda x: self.grammar._getAtomVarName(x), self.grammar.follow[atom.start_nt].difference({self.grammar.ε, self.grammar.σ, self.grammar.λ})))
            tpl[atom.start_nt.id]['escape_terminals'] = tpl[atom.start_nt.id]['escape_terminals'].union( escape_terminals )
          elif self.grammar.isSimpleTerminal(atom) or self.grammar.isNonTerminal(atom):
            tpl_rule['atoms'].append({
              'type': 'terminal' if self.grammar.isSimpleTerminal(atom) else 'nonterminal',
              'terminal_var_name': self.grammar._getAtomVarName(atom) if self.grammar.isSimpleTerminal(atom) else '',
              'nonterminal_func_name': '_' + str(atom).upper() if self.grammar.isNonTerminal(atom) else ''
            })
        tpl_nt['rules'].append( tpl_rule )
    return list(tpl.values())
  
  def getNudLed(self):
    nud = {}
    led = {}

    for terminal, rule in self.grammar.nud.items():
      nud[terminal.id] = self.ruletotpl(rule)
    for terminal, rule in self.grammar.led.items():
      led[terminal.id] = self.ruletotpl(rule)

    return {
      'led': led, 
      'nud': nud
    }
  
  def getDeclarations(self):
    tab = self.grammar._compute_parse_table()
    terminals = self.grammar._strip_abstract_terminals( self.grammar.terminals.copy() )

    terminal_str = {}
    terminal_var = {}
    for s,t in terminals.items():
      terminal_str[t.id] =  t.string
      terminal_var[t.id] = 'TERMINAL_' + str(t).strip("'").upper()

    nonterminal_str = {}
    nonterminal_var = {}
    for s,n in self.grammar.nonterminals.items():
      nonterminal_str[n.id] =  n.string
      nonterminal_var[n.id] = 'NONTERMINAL_' + str(n).upper()

    precedence= {}
    for t, bp in self.grammar.exprPrecedence.items():
      for b in bp:
        if b[1].upper() == 'LEFT' or b[1].upper() == 'RIGHT':
          precedence[t.id] = b[0]

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
      'nonterminal_var': nonterminal_var,
      'binding_power': precedence
    }

    return tpl
  
  def getEntryPoints(self):
    return {str(self.grammar.start).lower(): '_'+str(self.grammar.start).upper()}
  
  def getTokens(self):
    return self.tokens
  
  def getRules(self):
    return {r.id: r for r in self.grammar.normalized() if type(r) is not MacroGeneratedRule}
  
  def getExprRules(self):
    return {r.id: r for r in self.grammar.exprRules}
  
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