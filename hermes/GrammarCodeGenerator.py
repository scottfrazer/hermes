import re, moody
from pkg_resources import resource_filename
from hermes.Logger import Factory as LoggerFactory
from collections import OrderedDict

moduleLogger = LoggerFactory().getModuleLogger(__name__)

class Template:
  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)

  def _prepare(self, grammar):

    # Set the variable name for each terminal and nonterminal
    terminals = grammar.getSimpleTerminals()

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

  def render(self, grammar, addMain=False, initialTerminals=[]):
    templates_dir = resource_filename(__name__, 'templates')
    loader = moody.make_loader(templates_dir)
    self._prepare(grammar)
    LL1Nonterminals = [x for x in grammar.nonterminals if x not in map(lambda x: x.nonterminal, grammar.exprgrammars)]

    code = loader.render (
              self.template, \
              grammar = grammar, \
              LL1Nonterminals = LL1Nonterminals, \
              nonAbstractTerminals = grammar.getSimpleTerminals(), \
              addMain = addMain, \
              initialTerminals = initialTerminals
           )

    linereduce = re.compile('^[ \t]*$', re.M)
    code = linereduce.sub('', code)
    code = re.sub('\n+', '\n', code)
    return code

class PythonTemplate(Template):
  template = 'python/Parser.tpl'
  destination = 'Parser.py'

class CHeaderTemplate(Template):
  template = 'c/header.tpl'
  destination = 'parser.h'
  
class CSourceTemplate(Template):
  template = 'c/source.tpl'
  destination = 'parser.c'
