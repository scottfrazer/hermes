import re, json
from collections import OrderedDict
from hermes.Morpheme import NonTerminal, Terminal, EmptyString
from hermes.Grammar import CompositeGrammar, LL1GrammarFactory, ExpressionGrammarFactory
from hermes.Grammar import Rule, ExprRule, MacroGeneratedRule, Production, AstSpecification, AstTranslation
from hermes.Grammar import InfixOperator, PrefixOperator, MixfixOperator
from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, MinimumListMacro, OptionalMacro
from hermes.Logger import Factory as LoggerFactory

moduleLogger = LoggerFactory().getModuleLogger(__name__)

def pad( n, l ):
  t = int(n) - len(l)
  for x in range(t):
    l.append(None)
  return l

def flatten( l ):
  flat = []
  for x in l:
    flat.extend(x)
  return flat

class LL1MacroExpander:
  def __init__(self, terminalParser, nonTerminalParser):
    self.prefix = '_gen'
    self.id = 0
    self.nonTerminalParser = nonTerminalParser
    self.terminalParser = terminalParser
    self.list_cache = {}
    self.tlist_cache = {}
  
  def tlist( self, nonterminal, terminator ):
    rules = []

    key = tuple([str(nonterminal).lower(), str(terminator).lower()])
    if key in self.tlist_cache:
      return (self.tlist_cache[key][0].nonterminal, self.tlist_cache[key])
    
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt0.generated = True
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal, terminator, nt0] )), \
              MacroGeneratedRule(nt0, Production( [empty] )) ]
    self.tlist_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def slist( self, nonterminal, separator, minimum ):
    rules = []

    separator.isSeparator = True
    key = tuple([str(nonterminal).lower(), str(separator).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt1 = self.nonTerminalParser.parse( self.nextName() )
    nt0.generated = nt1.generated = True
    empty = self.terminalParser.parse('_empty')
    if minimum > 0:
      items = [nonterminal] * (2*minimum-1)
      for x in filter(lambda x: x % 2 == 1, range(2 * minimum - 1)): # all odd numbers in range
        items[x] = separator
      items.append(nt1)
    else:
      items = [nonterminal, nt1]
    rules = [ MacroGeneratedRule(nt0, Production( items )), \
              MacroGeneratedRule(nt1, Production( [separator, nonterminal, nt1] )), \
              MacroGeneratedRule(nt1, Production( [empty] )) ]
    if minimum == 0:
      rules.append( MacroGeneratedRule(nt0, Production( [empty] )) )
    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def nlist( self, nonterminal ):
    rules = []
    key = tuple([str(nonterminal).lower(), str(None).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt0.generated = True
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal, nt0] )), \
              MacroGeneratedRule(nt0, Production( [empty] )) ]
    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def mlist( self, nonterminal, minimum ):
    rules = []

    key = tuple([str(nonterminal).lower(), str(minimum).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])

    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt1 = self.nonTerminalParser.parse( self.nextName() )
    nt0.generated = nt1.generated = True
    empty = self.terminalParser.parse('_empty')
    prod = [nonterminal for x in range(minimum)]
    prod.append(nt1)
    rules = [ MacroGeneratedRule(nt0, Production( prod )), \
              MacroGeneratedRule(nt1, Production( [nonterminal, nt1] )), \
              MacroGeneratedRule(nt1, Production( [empty] )) ]
    if minimum == 0:
      rules.append( MacroGeneratedRule(nt0, Production( [empty] )) )
    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def optional( self, nonterminal ):
    rules = []

    key = tuple([str(nonterminal).lower(), str(None).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt0.generated = True
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal] )), \
              MacroGeneratedRule(nt0, Production( [empty] )) ]
    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def nextName(self):
    nt = self.prefix + str(self.id)
    self.id += 1
    return nt
  

class CachedParser:
  def __init__(self, parser):
    if not isinstance(parser, Parser):
      raise Exception('Expecting Parser object')
    self.parser = parser
    self.cache = dict()
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  def parse(self, string):
    normalized = self.parser.normalize(string)
    if normalized in self.cache:
      value = self.cache[normalized]
    else:
      value = self.parser.parse(normalized)
      self.cache[normalized] = value
    return value
  
  def getCache(self):
    return list(self.cache.values())
  

class Parser:
  def __init__(self):
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  def normalize(self, string):
    for regex, replacement in self.rnormalize.items():
      string = regex.sub( replacement, string )
    return string.lower().strip()
  

class RuleParser(Parser):
  replacements = OrderedDict([
        ("'|'", "'__Z_PIPE__'"),
        ("'+'", "'__Z_PLUS__'"),
        ("'->'", "'__Z_ARROW__'"),
        (' ', ''),
        ("\t", ''),
        ("\n", '')
      ])
  
  normalize = {
    re.compile(r'\s+'): ''
  }
  
  def __init__(self, atomParser, astParser):
    self.__dict__.update(locals())
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  def parse(self, string):
    rules = []
    for original, replacement in self.replacements.items():
      string = string.replace(original, replacement)
    (nonterminal, productions) = string.split(':=', 1)
    nonterminal = self.atomParser.parse(nonterminal)
    for production in productions.split('|'):
      (parsetree, ast) = pad(2, production.split('->'))
      morphemes = parsetree.replace("'__Z_PIPE__'", "'|'").split('+')
      morphemes = list(map(self.atomParser.parse, morphemes))
      ast = self.astParser.parse(ast)
      rules.append( Rule(nonterminal, Production(morphemes), 0, 0, ast) )
    return rules

class ExprRuleParser(RuleParser):
  ruleRegex = re.compile('^{([^}]*)}(\s*\+\s*{(.*)})?(->(.*))?$')

  def _getAtoms(self, string):
      if not string:
        return list()
      morphemes = string.replace("'__Z_PIPE__'", "'|'").split('+')
      return list(map(self.atomParser.parse, morphemes))

  def setBindingPower(self, bindingPower):
    self.__dict__.update(locals())

  def parse(self, string):
    rules = []
    for original, replacement in self.replacements.items():
      string = string.replace(original, replacement)
    (nonterminal, productions) = string.split(':=', 1)
    nonterminal = self.atomParser.parse(nonterminal)
    infixRegex = re.compile("^%s\s*\+\s*('[a-zA-Z_]+')\s*\+\s*%s\s*(->)?" % (nonterminal.string, nonterminal.string), re.I)
    prefixRegex = re.compile("^('[a-zA-Z_]+')\s*\+\s*%s\s*(->)?" % (nonterminal.string), re.I)
    for production in productions.split('|'):
      production = production.strip()

      match = infixRegex.match(production)
      if match:
        (parsetree, ast) = pad(2, production.split('->'))
        operator = self.atomParser.parse(match.group(1))
        ledMorphemes = [operator, nonterminal]
        ast = self.astParser.parse(ast)
        rules.append( ExprRule( nonterminal, Production(), Production(ledMorphemes), AstTranslation(0), ast, InfixOperator(operator) ))
        continue

      match = prefixRegex.match(production)
      if match:
        (parsetree, ast) = pad(2, production.split('->'))
        operator = self.atomParser.parse(match.group(1))
        nudMorphemes = [operator, nonterminal]
        ast = self.astParser.parse(ast)
        rules.append( ExprRule( nonterminal, Production(nudMorphemes), Production(), AstTranslation(0), ast, PrefixOperator(operator)) )
        continue

      match = self.ruleRegex.match(production)
      if not match:
        raise Exception('Invalidly formatted expression rule: %s' %(production))
      (nud, ledParseTree, ast) = (match.group(1), match.group(3), match.group(5))
      (nudParseTree, nudAst) = pad(2, nud.split('->'))
      nudMorphemes = self._getAtoms(nudParseTree)
      ledMorphemes = self._getAtoms(ledParseTree)
      operator = ledMorphemes[0] if len(ledMorphemes) else None
      if operator and not isinstance(operator, Terminal):
        raise Exception('Invalid operator for rule: %s' % (production))
      nudAst = self.astParser.parse(nudAst)
      ast = self.astParser.parse(ast)
      rules.append( ExprRule(nonterminal, Production(nudMorphemes), Production(ledMorphemes), nudAst, ast, MixfixOperator(operator)) )
    return rules

class AstParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): ''
  }
  
  def __init__(self, nonTerminalParser, terminalParser):
    self.__dict__.update(locals())
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  def parse(self, string):
    if not string:
      return AstTranslation(0)
    if '(' in string:
      (node, values) = string.replace(')', '').split('(')
      parameters = {}
      if len(values):
        for param in values.split(','):
          (name, value) = param.split('=')
          parameters[name] = ('$' if value == '$$' else int(value.replace('$', '')))
      return AstSpecification( node, parameters )
    else:
      index = '$' if string == '$$' else int(string.replace('$', ''))
      return AstTranslation( index )
  

class AtomParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): '',
    re.compile(r'\''): '',
    re.compile(r'\^'): '',
    re.compile(r'ε'): '_empty'
  }
  
  def __init__(self, nonTerminalParser, terminalParser, macroParser):
    self.__dict__.update(locals())
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)
  
  def parse(self, string):
    if string == 'ε' or string == '_empty':
      return self.terminalParser.parse( 'ε' )
    elif string[:5].lower() in ['tlist', 'mlist'] or string[:4].lower() == 'list' or string[:8] == 'optional':
      return self.macroParser.parse(string)
    elif string[0] == "'" or (string[0] == '^' and string[1] == "'"): # Terminal
      return self.terminalParser.parse( string.replace("'", "").replace('^', '') )
    else: # Nonterminal
      return self.nonTerminalParser.parse( string )
  

class MacroParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): ''
  }
  
  def __init__(self, nonTerminalParser, terminalParser, sListMacroParser, nListMacroParser, tListMacroParser, mListMacroParser, optionalMacroParser, expand=True):
    self.__dict__.update(locals())
    self.logger = LoggerFactory().getClassLogger(__name__, self.__class__.__name__)

  def parse(self, string):
    self.logger.debug('Parsing macro %s' % (string))
    if string[:5].lower() == 'tlist':
      macro = self.tListMacroParser.parse(string, self.expand)
    elif string[:5].lower() == 'mlist':
      macro = self.mListMacroParser.parse(string, self.expand)
    elif string[:8].lower() == 'optional':
      macro = self.optionalMacroParser.parse(string, self.expand)
    elif string[:4].lower() == 'list':
      (nonterminal, separator, minimum) = pad(3, string[5:-1].split(','))
      if separator:
        macro = self.sListMacroParser.parse(string, self.expand)
      else:
        macro = self.nListMacroParser.parse(string, self.expand)
    self.logger.debug('Parsed macro: %s' % (macro))
    return macro

class sListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string, expand=True):
    (nonterminal, separator, minimum) = pad(3, string[5:-1].split(','))
    if not nonterminal or not separator:
      raise Exception('bah you did things wrong: %s' %(string))

    nonterminal = self.nonTerminalParser.parse(nonterminal)
    separator = self.terminalParser.parse(separator.replace("'", ''))
    minimum = int(minimum) if minimum else 0

    (start, rules) = (None, None)
    if expand:
      (start, rules) = self.macroExpander.slist( nonterminal, separator, minimum )

    macro = SeparatedListMacro( nonterminal, separator, start, rules )

    if rules:
      for rule in rules:
        rule.nonterminal.macro = macro

    return macro

class nListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string, expand=True):
    nonterminal = self.nonTerminalParser.parse(string[5:-1])

    (start, rules) = (None, None)
    if expand:
      (start, rules) = self.macroExpander.nlist( nonterminal )

    macro = NonterminalListMacro( nonterminal, start, rules )

    if rules:
      for rule in rules:
        rule.nonterminal.macro = macro

    return macro

class tListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string, expand=True):
    (nonterminal, terminator) = pad(2, string[6:-1].split(','))
    if not nonterminal or not terminator:
      raise Exception('bah, bad')
    terminator = self.terminalParser.parse(terminator.replace("'", ''))
    nonterminal = self.nonTerminalParser.parse(nonterminal)

    (start, rules) = (None, None)
    if expand:
      (start, rules) = self.macroExpander.tlist( nonterminal, terminator )

    macro = TerminatedListMacro( nonterminal, terminator, start, rules)

    if rules:
      for rule in rules:
        rule.nonterminal.macro = macro

    return macro

class mListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string, expand=True):
    (nonterminal, minimum) = pad(2, string[6:-1].split(','))
    if not nonterminal or not minimum:
      raise Exception('bah, bad')
    minimum = int(minimum.replace("'", ''))
    nonterminal = self.nonTerminalParser.parse(nonterminal)

    (start, rules) = (None, None)
    if expand:
      (start, rules) = self.macroExpander.mlist( nonterminal, minimum )

    macro = MinimumListMacro( nonterminal, minimum, start, rules)

    # TODO: I'm setting the .macro attribute because I need it to 
    # determine how to make the AST for the resulting parsetree.  
    # There should be a better way to achieve this.

    if rules:
      for rule in rules:
        rule.nonterminal.macro = macro

    return macro

class optionalMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string, expand=True):
    nonterminal = self.nonTerminalParser.parse(string[9:-1])

    (start, rules) = (None, None)
    if expand:
      (start, rules) = self.macroExpander.optional( nonterminal )

    macro = OptionalMacro( nonterminal, start, rules )

    if rules:
      for rule in rules:
        rule.nonterminal.macro = macro

    return macro

class NonTerminalParser(AtomParser):
  def __init__(self):
    pass
  
  def parse(self, string):
    nonterminal = NonTerminal( string.replace("'", '') )
    return nonterminal
  

class TerminalParser(AtomParser):
  def __init__(self):
    pass
  
  def parse(self, string):
    if string == 'ε' or string == '_empty':
      return EmptyString(-1)
    else:
      return Terminal( string.replace("'", '') )
  

class HermesParser:
  def __init__( self, ruleParser, exprRuleParser, terminalParser, nonTerminalParser, macroParser ):
    self.__dict__.update(locals())
  def parseRule( self, string ):
    return self.ruleParser.parse(string)
  def _setBindingPower( self, bindingPower ):
    self.exprRuleParser.setBindingPower(bindingPower)
  def parseExprRule( self, string ):
    return self.exprRuleParser.parse(string)
  def parseNonTerminal( self, string ):
    return self.nonTerminalParser.parse(string)
  def parseTerminal( self, string ):
    return self.terminalParser.parse(string)
  def getTerminals( self ):
    return self.terminalParser.getCache()
  def getNonTerminals( self ):
    return self.nonTerminalParser.getCache()
  def getMacros( self ):
    return self.macroParser.getCache()

class HermesParserFactory:
  def create(self):
    tParser = CachedParser( TerminalParser() )
    nParser = CachedParser( NonTerminalParser() )
    macroExpander = LL1MacroExpander(tParser, nParser)
    sListParser = sListMacroParser(nParser, tParser, macroExpander)
    nListParser = nListMacroParser(nParser, tParser, macroExpander)
    tListParser = tListMacroParser(nParser, tParser, macroExpander)
    mListParser = mListMacroParser(nParser, tParser, macroExpander)
    optionalParser = optionalMacroParser(nParser, tParser, macroExpander)
    mParser = CachedParser( MacroParser(nParser, tParser, sListParser, nListParser, tListParser, mListParser, optionalParser) )
    astParser = AstParser(nParser, tParser)
    atomParser = AtomParser(nParser, tParser, mParser) 
    exprAtomParser = AtomParser(nParser, tParser, mParser) 
    ruleParser = RuleParser(atomParser, astParser)
    exprRuleParser = ExprRuleParser(exprAtomParser, astParser)
    return HermesParser(ruleParser, exprRuleParser, tParser, nParser, mParser)
  def getExprRuleParser(self):
    tParser = CachedParser( TerminalParser() )
    nParser = CachedParser( NonTerminalParser() )
    macroExpander = LL1MacroExpander(tParser, nParser)
    sListParser = sListMacroParser(nParser, tParser, macroExpander)
    nListParser = nListMacroParser(nParser, tParser, macroExpander)
    tListParser = tListMacroParser(nParser, tParser, macroExpander)
    mListParser = mListMacroParser(nParser, tParser, macroExpander)
    optionalParser = optionalMacroParser(nParser, tParser, macroExpander)
    mParser = CachedParser( MacroParser(nParser, tParser, sListParser, nListParser, tListParser, mListParser, optionalParser) )
    exprAtomParser = AtomParser(nParser, tParser, mParser) 
    astParser = AstParser(nParser, tParser)
    return ExprRuleParser(exprAtomParser, astParser)

class GrammarFileParser:
  def __init__( self, hermesParser ):
    self.hermesParser = hermesParser
  
  def normalize( self, json ):
    if 'll1' not in json:
      json['ll1'] = dict()
    elif not isinstance(json['ll1'], dict):
      raise Exception("json['ll1'] expected to be object")

    if 'rules' not in json['ll1']:
      json['ll1']['rules'] = list()
    elif not isinstance(json['ll1']['rules'], list):
      raise Exception("json['ll1']['rules'] expected to be object")

    if 'start' not in json['ll1'] or len(json['ll1']['start']) == 0:
      raise Exception("json['ll1']['start'] expected to be non-empty string")

    if 'expr' not in json:
      json['expr'] = list()
    elif not isinstance(json['expr'], list):
      raise Exception("json['expr'] expected to be list")

    json['ll1']['rules'] = flatten(list(map(self.hermesParser.parseRule, json['ll1']['rules'])))
    json['ll1']['start'] = self.hermesParser.parseNonTerminal(json['ll1']['start'])

    for (i, parser) in enumerate(json['expr']):
      if not isinstance(parser, dict):
        raise Exception("json['expr'][*] expected to be an object")
      if 'nonterminal' not in parser:
        raise Exception("json['expr'][%d]['nonterminal'] does not exist" % (i))

      json['expr'][i]['nonterminal'] = self.hermesParser.parseNonTerminal(parser['nonterminal'])

      if 'binding_power' not in parser:
        json['expr'][i]['binding_power'] = list()
      elif not isinstance(parser['binding_power'], list):
        raise Exception("json['binding_power'] expected to be a list")

      for (j, binding_power) in enumerate(parser['binding_power']):

        if 'terminals' not in binding_power:
          json['expr'][i]['binding_power'][j]['terminals'] = list()
        elif not isinstance(binding_power['terminals'], list):
          raise Exception("json['expr'][i]['binding_power'][j]['terminals'] expected to be a list")

        value = json['expr'][i]['binding_power'][j]['terminals']
        json['expr'][i]['binding_power'][j]['terminals'] = \
          list(map(self.hermesParser.parseTerminal, value))

      self.hermesParser._setBindingPower( json['expr'][i]['binding_power'] )

      if 'rules' not in parser:
        json['expr'][i]['rules'] = list()
      elif not isinstance(parser['rules'], list):
        raise Exception("json['expr'] expected to be a list")

      json['expr'][i]['rules'] = flatten(list(map(self.hermesParser.parseExprRule, parser['rules'])))

    json['global'] = dict()
    json['global']['nonterminals'] = set(self.hermesParser.getNonTerminals())
    json['global']['terminals'] = set(self.hermesParser.getTerminals())
    json['global']['macros'] = set(self.hermesParser.getMacros())
    return json
  
  def parse( self, fp, start=None ):
    contents = json.load(fp)
    fp.close()

    ll1GrammarFactory = LL1GrammarFactory()
    exprGrammarFactory = ExpressionGrammarFactory()

    normalized = self.normalize(contents)
    start = self.hermesParser.parseNonTerminal(start) if start else contents['ll1']['start']

    ll1Grammar = ll1GrammarFactory.create(
      normalized['global']['nonterminals'], \
      normalized['global']['terminals'], \
      normalized['global']['macros'], \
      set(normalized['ll1']['rules']), \
      normalized['ll1']['start']
    )

    exprGrammars = []
    parentGrammars = dict()
    for grammar in normalized['expr']:
      exprGrammar = exprGrammarFactory.create(
        normalized['global']['nonterminals'], \
        normalized['global']['terminals'], \
        normalized['global']['macros'], \
        set(grammar['rules']), \
        grammar['binding_power'], \
        grammar['nonterminal']
      )
      exprGrammars.append(exprGrammar)
      if 'extends' in grammar:
        parentGrammars[exprGrammar] = grammar['extends']
    
    for grammar, parent in parentGrammars.items():
      for grammar2 in exprGrammars:
        if grammar2.nonterminal.string == parent:
          grammar.extend(grammar2)

    return CompositeGrammar(ll1Grammar, exprGrammars)

