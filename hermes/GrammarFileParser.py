import re, json, sys
from collections import OrderedDict
from hermes.Morpheme import NonTerminal, Terminal, EmptyString, EndOfStream, Expression
from hermes.Grammar import Grammar, LL1Grammar, CompositeGrammar, ExpressionGrammar
from hermes.Grammar import Rule, MacroGeneratedRule, Production, AstSpecification, AstTranslation
from hermes.Macro import ExprListMacro, SeparatedListMacro, NonterminalListMacro

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
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal, terminator, nt0] )), \
              MacroGeneratedRule(nt0, Production( [empty] )) ]
    self.tlist_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def slist( self, nonterminal, separator ):
    rules = []

    key = tuple([str(nonterminal).lower(), str(separator).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    nt1 = self.nonTerminalParser.parse( self.nextName() )
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal, nt1] )), \
              MacroGeneratedRule(nt0, Production( [empty] )), \
              MacroGeneratedRule(nt1, Production( [separator, nonterminal, nt1] )), \
              MacroGeneratedRule(nt1, Production( [empty] )) ]
    self.list_cache[key] = rules
    return (rules[0].nonterminal, rules)
  
  def nlist( self, nonterminal ):
    rules = []

    key = tuple([str(nonterminal).lower(), str(None).lower()])
    if key in self.list_cache:
      return (self.list_cache[key][0].nonterminal, self.list_cache[key])
    nt0 = self.nonTerminalParser.parse( self.nextName() )
    empty = self.terminalParser.parse('_empty')
    rules = [ MacroGeneratedRule(nt0, Production( [nonterminal, nt0] )), \
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
  
  def parse(self, string):
    rules = []
    for original, replacement in self.replacements.items():
      string = string.replace(original, replacement)
    (nonterminal, productions) = string.split(':=', 1)
    nonterminal = self.atomParser.parse(nonterminal)
    for production in productions.split('|'):
      (parsetree, ast) = pad(2, production.split('->'))
      morphemes = parsetree.replace("'__Z_PIPE__'", "'|'").split('+')
      root = self.getRoot(morphemes)
      morphemes = list(map(self.atomParser.parse, morphemes))
      ast = self.astParser.parse(ast)
      rules.append( Rule(nonterminal, Production(morphemes), 0, root, ast) )
    return rules
  
  def getRoot( self, morphemes ):
    for idx, morpheme in enumerate(morphemes):
      try:
        if morpheme[0] == '^':
          return idx
      except:
        pass
    return 0
  

class AstParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): ''
  }
  
  def __init__(self, nonTerminalParser, terminalParser):
    self.__dict__.update(locals())
  
  def parse(self, string):
    if not string:
      return None
    if '(' in string:
      (node, values) = string.replace(')', '').split('(')
      parameters = {}
      for param in values.split(','):
        (name, value) = param.split('=')
        parameters[name] = int(value.replace('$', ''))
      return AstSpecification( node, parameters )
    else:
      return AstTranslation( int(string.replace('$', '')) )
  

class AtomParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): '',
    re.compile(r'\''): '',
    re.compile(r'\^'): '',
    re.compile(r'ε'): '_empty'
  }
  
  def __init__(self, nonTerminalParser, terminalParser, macroParser):
    self.__dict__.update(locals())
  
  def parse(self, string):
    if string == 'ε' or string == '_empty':
      return self.terminalParser.parse( 'ε' )
    elif string[:5].lower() == 'tlist' or string[:4].lower() == 'list':
      return self.macroParser.parse(string)
    elif string[0] == "'" or (string[0] == '^' and string[1] == "'"): # Terminal
      return self.terminalParser.parse( string.replace("'", "").replace('^', '') )
    else: # Nonterminal
      return self.nonTerminalParser.parse( string )
  

class MacroParser(Parser):
  rnormalize = {
    re.compile(r'\s+'): ''
  }
  
  def __init__(self, nonTerminalParser, terminalParser, sListMacroParser, nListMacroParser, tListMacroParser):
    self.__dict__.update(locals())
  
  def parse(self, string):
    if string[:5].lower() == 'tlist':
      return self.tListMacroParser.parse(string)
    elif string[:4].lower() == 'list':
      (nonterminal, separator) = pad(2, string[5:-1].split(','))
      if separator:
        return self.sListMacroParser.parse(string)
      else:
        return self.nListMacroParser.parse(string)
  

class sListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string):
    (nonterminal, separator) = pad(2, string[5:-1].split(','))
    if not nonterminal or not separator:
      raise Exception('bah you did things wrong: %s' %(string))
    
    nonterminal = self.nonTerminalParser.parse(nonterminal)
    separator = self.terminalParser.parse(separator.replace("'", ''))
    (start, rules) = self.macroExpander.slist( nonterminal, separator )
    context = 'expr' if str(nonterminal).lower() == '_expr' else 'll1'

    if str(nonterminal).lower() == '_expr':
      macro = ExprListMacro( nonterminal, separator )
    else:
      macro = SeparatedListMacro( nonterminal, separator, start, rules )
    rules[0].nonterminal.macro = macro
    rules[2].nonterminal.macro = macro
    return macro
  

class nListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string):
    nonterminal = self.nonTerminalParser.parse(string[5:-1])
    (start, rules) = self.macroExpander.nlist( nonterminal )
    macro = NonterminalListMacro( nonterminal, start, rules )
    rules[0].nonterminal.macro = macro
    return macro
  

class tListMacroParser(MacroParser):
  def __init__(self, nonTerminalParser, terminalParser, macroExpander):
    self.__dict__.update(locals())
  
  def parse(self, string):
    (nonterminal, terminator) = pad(2, string[6:-1].split(','))
    if not nonterminal or not terminator:
      raise Exception('bah, bad')
    terminator = self.terminalParser.parse(terminator.replace("'", ''))
    nonterminal = self.nonTerminalParser.parse(nonterminal)
    (start, rules) = self.macroExpander.tlist( nonterminal, terminator )
    macro = TerminatedListMacro( nonterminal, terminator, start, rules)
    rules[0].nonterminal.macro = macro
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
  def __init__( self, ruleParser, terminalParser, nonTerminalParser, macroParser ):
    self.__dict__.update(locals())
  def parseRule( self, string ):
    return self.ruleParser.parse(string)
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
    mParser = CachedParser( MacroParser(nParser, tParser, sListParser, nListParser, tListParser) )
    astParser = AstParser(nParser, tParser)
    atomParser = AtomParser(nParser, tParser, mParser) 
    ruleParser = RuleParser(atomParser, astParser)
    return HermesParser(ruleParser, tParser, nParser, mParser)
  

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

      if 'rules' not in parser:
        json['expr'][i]['rules'] = list()
      elif not isinstance(parser['rules'], list):
        raise Exception("json['expr'] expected to be a list")

      json['expr'][i]['rules'] = flatten(list(map(self.hermesParser.parseRule, parser['rules'])))

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

    json['global'] = dict()
    json['global']['nonterminals'] = set(self.hermesParser.getNonTerminals())
    json['global']['terminals'] = set(self.hermesParser.getTerminals())
    json['global']['macros'] = set(self.hermesParser.getMacros())
    return json
  
  def parse( self, fp, start=None ):
    contents = json.load(fp)
    fp.close()

    normalized = self.normalize(contents)

    start = self.hermesParser.parseNonTerminal(start) if start else contents['ll1']['start']
    ll1Grammar = LL1Grammar( normalized['global']['nonterminals'], \
                             normalized['global']['terminals'], \
                             normalized['global']['macros'], \
                             set(normalized['ll1']['rules']), \
                             normalized['ll1']['start'] )
    exprGrammars = []
    for grammar in normalized['expr']:
      exprGrammars.append( ExpressionGrammar( \
                             normalized['global']['nonterminals'], \
                             normalized['global']['terminals'], \
                             normalized['global']['macros'], \
                             set(grammar['rules']), \
                             grammar['binding_power'], \
                             grammar['nonterminal'] ))

    return CompositeGrammar(ll1Grammar, exprGrammars)
  
