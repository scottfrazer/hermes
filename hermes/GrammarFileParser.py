import re, json
from collections import OrderedDict
from hermes.Grammar import Grammar
from hermes.Morpheme import NonTerminal
from hermes.Morpheme import Terminal
from hermes.Morpheme import EmptyString
from hermes.Morpheme import EndOfStream
from hermes.Morpheme import Expression
from hermes.Grammar import Rule, MacroGeneratedRule
from hermes.Grammar import Production
from hermes.Grammar import AstSpecification
from hermes.Grammar import AstTranslation
from hermes.Macro import ExprListMacro, SeparatedListMacro, NonterminalListMacro
from hermes.Factory import Factory

class LL1MacroExpander:
  def __init__(self, registry):
    self.prefix = '_gen'
    self.id = 0
    self.list_cache = {}
    self.registry = registry
  
  # TODO: this macro assumes that the first argument is a nonterminal and second is a terminal.  Make this more general case
  def list( self, nonterminal, separator ):
    rules = []

    key = tuple([str(nonterminal).upper(), str(separator).upper()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    
    nt0 = self.registry.addNonTerminal( self.makeTmpNonTerminal() )

    if not separator:
      rules.append( self.registry.addMacroGeneratedRule( nt0, Production( [nonterminal, nt0] )) )
      rules.append( self.registry.addMacroGeneratedRule( nt0, Production( [self.registry.addEmptyString()] ) ) )

    else:
      nt1 = self.registry.addNonTerminal( self.makeTmpNonTerminal() )
      rules.append( self.registry.addMacroGeneratedRule( nt0, Production( [nonterminal, nt1] )) )
      rules.append( self.registry.addMacroGeneratedRule( nt0, Production( [self.registry.addEmptyString()] )) )
      rules.append( self.registry.addMacroGeneratedRule( nt1, Production( [separator, nonterminal, nt1] )) )
      rules.append( self.registry.addMacroGeneratedRule( nt1, Production( [self.registry.addEmptyString()] ) ) )

    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def makeTmpNonTerminal(self):
    nt = self.prefix + str(self.id)
    self.id += 1
    return nt
  

class GrammarFileParser:
  def __init__(self):
    self.replacements = OrderedDict([
        ("'|'", "'__Z_PIPE__'"),
        ("'+'", "'__Z_PLUS__'"),
        ("'->'", "'__Z_ARROW__'"),
        (' ', ''),
        ("\t", ''),
        ("\n", '')
      ])
  
  def parse( self, fp, start=None ):
    contents = json.load(fp)
    fp.close()
    self.factory = Factory()
    self.ll1MacroExpander = LL1MacroExpander(self.factory)

    if 'll1' in contents and 'rules' in contents['ll1']:
      for rule in contents['ll1']['rules']:
        self.parseRule(rule, self.factory.addRule)
    
    if 'expr' in contents:
      if 'rules' in contents['expr']:
        for rule in contents['expr']['rules']:
          self.parseRule(rule, self.factory.addExpressionRule)
      if 'binding_power' in contents['expr']:
        for binding_power in contents['expr']['binding_power']:
          for token in binding_power['terminals']:
            terminal = self.factory.addTerminal( token.replace("'", "") )
            self.factory.addOperatorPrecedence( terminal, binding_power['associativity'].lower() )
    if start:
      start_nt = self.factory.nonterminals[start.lower()]
    elif 'll1' in contents and 'start' in contents['ll1']:
      start_nt = self.factory.nonterminals[contents['ll1']['start'].lower()]
    return self.factory.buildGrammar( start_nt )
  
  def parseRule( self, string, addFunc ):
    for original, replacement in self.replacements.items():
      string = string.replace(original, replacement)
    (nonterminal, productions) = string.split(':=', 1)
    nonterminal = self.factory.addNonTerminal(nonterminal)
    for production in productions.split('|'):
      (parsetree, ast) = self.pad(2, production.split('->'))
      morphemes = parsetree.replace("'__Z_PIPE__'", "'|'").split('+')
      morphemes = list(map(self.strToMorpheme, morphemes))
      ast = self.strToAst(ast)
      addFunc( nonterminal, Production(morphemes), self.getRoot(morphemes), ast )
  
  def getRoot( self, morphemes ):
    for idx, morpheme in enumerate(morphemes):
      try:
        if morpheme.root:
          return idx
      except:
        pass
    return 0
  
  def strToAst(self, ast):
    if not ast:
      return None
    if '(' in ast:
      (node, values) = ast.replace(')', '').split('(')
      parameters = {}
      for param in values.split(','):
        (name, value) = param.split('=')
        parameters[name] = int(value.replace('$', ''))
      return AstSpecification( node, parameters )
    else:
      return AstTranslation( int(ast.replace('$', '')) )
  
  def strToMorpheme(self, string):
    if string[0] == 'ε' or string == '_empty':
      return self.factory.ε

    if string[:4].lower() == 'list':
      (nonterminal, separator) = self.pad(2, string[5:-1].split(','))

      if separator:
        separator = self.factory.addTerminal(separator.replace("'", ''))
      else:
        separator = None

      if nonterminal:
        nonterminal = self.factory.addNonTerminal(nonterminal)
      else:
        raise Exception('Nonterminal needs to be specified as first argument in \'list\' macro')

      (start, rules) = self.ll1MacroExpander.list( nonterminal, separator )
      context = 'expr' if str(nonterminal).lower() == '_expr' else 'll1'
      return self.factory.addListMacro( nonterminal, separator, start, rules, context )

    elif string[0] == "'" or (string[0] == '^' and string[1] == "'"): # Terminal
      return self.factory.addTerminal( string.replace("'", "").replace('^', ''), string[0] == '^' )

    else: # Nonterminal
      return self.factory.addNonTerminal( string, string[0] == '^' )
  
  def pad( self, n, l ):
    t = int(n) - len(l)
    for x in range(t):
      l.append(None)
    return l
  
      
