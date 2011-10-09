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

  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)

  def _prepare(self, grammar):
    tab = grammar._compute_parse_table()
    terminals = grammar._strip_abstract_terminals( grammar.terminals.copy() )
    parseTable = ',\n  '.join(['[' + ', '.join([str(r.id) if r else str(-1) for r in tab[i]]) + ']' for i in range(len(grammar.nonterminals))])

    for terminal in terminals:
      terminal.varname = 'TERMINAL_' + str(terminal).strip("'").upper()

    for nonterminal in grammar.nonterminals:
      nonterminal.varname = 'NONTERMINAL_' + str(nonterminal).upper()

    # Operator precedence
    for index, egrammar in enumerate(grammar.getExpressionGrammars()):
      infixPrecedence = dict()
      prefixPrecedence = dict()
      for terminal, precedence in egrammar.getPrecedence().items():
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

      egrammar.infix = infix
      egrammar.prefix = prefix

    #  LL1 Rule helpers
    exprNonTerminals = list(map(lambda x: x.nonterminal, grammar.getExpressionGrammars()))
    for nonterminal in grammar.nonterminals:
      if nonterminal in exprNonTerminals:
        continue
      nonterminal.empty = False
      nonterminal.rules = grammar.getExpandedLL1Rules(nonterminal)
      for rule in nonterminal.rules:
        rule.empty = False
        if len(rule.production.morphemes) == 1 and rule.production.morphemes[0] == grammar.ε:
          rule.empty = True
          nonterminal.empty = True
      nonterminal.rules = list(filter(lambda x: not x.empty, nonterminal.rules))

    return (terminals, parseTable)

  def render(self, grammar, addMain=False, entryPoints=[], initialTerminals=[]):
    templates_dir = resource_filename(__name__, 'templates')
    loader = moody.make_loader(templates_dir)
    (terminals, parseTable) = self._prepare(grammar)
    nonExpressionNonterminals = [x for x in grammar.nonterminals if x not in map(lambda x: x.nonterminal, grammar.exprgrammars)]

    code = loader.render (
              self.template, \
              grammar = grammar, \
              nonExpressionNonterminals = nonExpressionNonterminals, \
              nonAbstractTerminals = terminals, \
              parseTable = parseTable, \
              addMain = addMain, \
              entryPoints = entryPoints, \
              initialTerminals = initialTerminals
           )

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
