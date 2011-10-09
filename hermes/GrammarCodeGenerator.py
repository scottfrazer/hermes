from os import path
import re
from pkg_resources import resource_filename
from types import *
from hermes.Morpheme import Terminal, NonTerminal, EmptyString
from hermes.Macro import NonterminalListMacro, SeparatedListMacro
from hermes.Grammar import MacroGeneratedRule, AstSpecification, AstTranslation
from hermes.Logger import Factory as LoggerFactory
from collections import OrderedDict
import moody

moduleLogger = LoggerFactory().getModuleLogger(__name__)

class Template:
  pass

class PythonTemplate(Template):
  template = 'python/Parser.tpl'
  destination = 'Parser.py'
  def __init__(self, resources):
    self.resources = resources
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  def render(self, grammar):
    x = { 
      'tokens': self.resources.getTokens(),
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
    nonExpressionNonterminals = [x for x in grammar.nonterminals if x not in map(lambda x: x.nonterminal, grammar.exprgrammars)]
    code = loader.render( self.template, nonExpressionNonterminals=nonExpressionNonterminals, grammar=grammar, add_main=x['add_main'], expr_rules=x['expr_rules'], tokens=x['tokens'], entry=x['entry'], nt=x['parser'], init=x['init'], entry_points=x['entry_points'], nudled=x['nudled'])
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
  
  def getEntry(self):
    return str(self.grammar.getLL1Grammar().getStart()).lower()
  
  def getParser(self):
    exprNonTerminals = list(map(lambda x: x.nonterminal, self.grammar.getExpressionGrammars()))
    for nonterminal in self.grammar.nonterminals:
      if nonterminal in exprNonTerminals:
        continue
      nonterminal.empty = False
      nonterminal.rules = self.grammar.getExpandedLL1Rules(nonterminal)
      nonterminal.escape_terminals = set() # TODO: is this needed???
      for rule in nonterminal.rules:
        rule.empty = False
        if len(rule.production.morphemes) == 1 and rule.production.morphemes[0] == self.grammar.ε:
          rule.empty = True
          nonterminal.empty = True
      nonterminal.rules = list(filter(lambda x: not x.empty, nonterminal.rules))
  
  def getNudLed(self):
    templates = []
    for index, grammar in enumerate(self.grammar.getExpressionGrammars()):
      infixPrecedence = dict()
      prefixPrecedence = dict()
      for terminal, precedence in grammar.getPrecedence().items():
        for p in precedence:
          if p.associativity in ['left', 'right']:
            infixPrecedence[terminal] = p.precedence
          if p.associativity == 'unary':
            prefixPrecedence[terminal] = p.precedence

      infix = OrderedDict()
      prefix = OrderedDict()

      for key in sorted(infixPrecedence, key=lambda x: x.id):
        infix[key.id] = infixPrecedence[key]
      for key in sorted(prefixPrecedence, key=lambda x: x.id):
        prefix[key.id] = prefixPrecedence[key]

      tpl = {
        'index': index,
        'grammar': grammar,
        'infixPrecedence': infix,
        'prefixPrecedence': prefix
      }

      templates.append(tpl)
    return sorted(templates, key=lambda x: x['index'])
  
  def getDeclarations(self):
    tab = self.grammar._compute_parse_table()
    terminals = self.grammar._strip_abstract_terminals( self.grammar.terminals.copy() )

    terminal_str = OrderedDict()
    terminal_var = OrderedDict()
    for t in sorted(terminals, key=lambda x: str(x)):
      terminal_str[t.id] =  t.string
      terminal_var[t.id] = 'TERMINAL_' + str(t).strip("'").upper()

    nonterminal_str = OrderedDict()
    nonterminal_var = OrderedDict()
    for n in sorted(self.grammar.nonterminals, key=lambda x: str(x)):
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
  
  def getExprGrammars(self):
    return self.grammar.getExpressionGrammars()
  

class GrammarCodeGenerator:
  def __init__(self, template, directory):
    self.template = template
    self.directory = directory
  
  def generate( self, grammar ):
    #try:
      fp = open( path.join( self.directory, self.template.destination ), 'w' )
      fp.write( self.template.render(grammar) )
      fp.close()
      return True
    #except:
    #  return False
