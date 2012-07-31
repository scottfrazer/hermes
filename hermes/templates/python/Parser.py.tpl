import sys, inspect
from ParserCommon import *

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

def whoami():
  return inspect.stack()[1][3]
def whosdaddy():
  return inspect.stack()[2][3]
def parse( iterator, entry ):
  p = {{prefix}}Parser()
  return p.parse(iterator, entry)

{% for exprGrammar in grammar.exprgrammars %}
class {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}:
  def __init__(self, parent):
    self.__dict__.update(locals())

    self.infixBp = {
      {% for terminal_id, binding_power in exprGrammar.infix.items() %}
      {{terminal_id}}: {{binding_power}},
      {% endfor %}
    }

    self.prefixBp = {
      {% for terminal_id, binding_power in exprGrammar.prefix.items() %}
      {{terminal_id}}: {{binding_power}},
      {% endfor %}
    }

  def getInfixBp(self, tokenId):
    try:
      return self.infixBp[tokenId]
    except:
      return 0

  def getPrefixBp(self, tokenId):
    try:
      return self.prefixBp[tokenId]
    except:
      return 0
  
  def getCurrentToken(self):
    return self.parent.tokens.current()

  def expect(self, token):
    return self.parent.expect(token)

  def parse(self, rbp = 0):
    left = self.nud()
    if isinstance(left, ParseTree):
      left.isExpr = True
      left.isNud = True
    while self.getCurrentToken() and rbp < self.getInfixBp(self.getCurrentToken().getId()):
      left = self.led(left)
    if left:
      left.isExpr = True
    return left

  def nud(self):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    if not current:
      return tree

    {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
      {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

      {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

      {% if len(ruleFirstSet) and not isOptional %}
    {{'if' if i == 0 else 'elif'}} current.getId() in [{{', '.join([str(x.id) for x in exprGrammar.ruleFirst(rule)])}}]:
      # {{rule}}
        {% if isinstance(rule.nudAst, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.nudAst.name}}', {{rule.nudAst.parameters}})
        {% elif isinstance(rule.nudAst, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.nudAst.idx}})
        {% endif %}

      tree.nudMorphemeCount = {{len(rule.nudProduction)}}

        {% for morpheme in rule.nudProduction.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}( self.getPrefixBp({{rule.operator.operator.id}}) ) )
      tree.isPrefix = True
            {% else %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}() )
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self.parent.parse_{{morpheme.string.lower()}}() )
          {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self.parent.parse_{{morpheme.start_nt.string.lower()}}() )
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

  def led(self, left):
    tree = ParseTree( NonTerminal({{exprGrammar.nonterminal.id}}, '{{exprGrammar.nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    {% py seen = list() %}
    {% for rule in exprGrammar.getExpandedExpressionRules() %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) and led[0] not in seen %}

    {{'if' if len(seen)==0 else 'else if'}} current.getId() == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

        {% if len(rule.nudProduction) == 1 and isinstance(rule.nudProduction.morphemes[0], NonTerminal) %}
          {% py nt = rule.nudProduction.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
      tree.isExprNud = True 
          {% endif %}
        {% endif %}

      tree.add(left)

        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
      modifier = {{1 if rule.operator.operator.id in exprGrammar.precedence and exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}}
            {% if isinstance(rule.operator, InfixOperator) %}
      tree.isInfix = True
            {% endif %}
      tree.add( self.parent.parse_{{rule.nonterminal.string.lower()}}( self.getInfixBp({{rule.operator.operator.id}}) - modifier ) )
          {% elif isinstance(morpheme, NonTerminal) %}
      tree.add( self.parent.parse_{{morpheme.string.lower()}}() )
          {% elif isinstance(morpheme, LL1ListMacro) %}
      tree.add( self.parent.parse_{{morpheme.start_nt.string.lower()}}() )
          {% endif %}
        {% endfor %}
      return tree
      {% endif %}
    {% endfor %}

    return tree
{% endfor %}

class {{prefix}}Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
  {% for terminal in nonAbstractTerminals %}
    {{terminal.id}}: '{{terminal.string}}',
  {% endfor %}

  {% for terminal in nonAbstractTerminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
  {% endfor %}
  }

  # Quark - finite string set maps one string to exactly one int, and vice versa
  nonterminals = {
  {% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: '{{nonterminal.string}}',
  {% endfor %}

  {% for nonterminal in grammar.nonterminals %}
    '{{nonterminal.string.lower()}}': {{nonterminal.id}},
  {% endfor %}
  }

  # table[nonterminal][terminal] = rule
  table = [
    {% py parseTable = grammar.getParseTable() %}
    {% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}}],
    {% endfor %}
  ]

  {% for terminal in nonAbstractTerminals %}
  TERMINAL_{{terminal.string.upper()}} = {{terminal.id}}
  {% endfor %}

  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()

  def isTerminal(self, id):
    return 0 <= id <= {{len(nonAbstractTerminals) - 1}}

  def isNonTerminal(self, id):
    return {{len(nonAbstractTerminals)}} <= id <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}}

  def parse(self, tokens):
    self.tokens = tokens
    self.start = '{{str(grammar.start).upper()}}'
    tree = self.parse_{{str(grammar.start).lower()}}()
    if self.tokens.current() != None:
      raise SyntaxError( 'Finished parsing without consuming all tokens.' )
    return tree

  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError( 'No more tokens.  Expecting %s' % (self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError( 'Unexpected symbol when parsing %s.  Expected %s, got %s.' %(whosdaddy(), self.terminals[terminalId], currentToken if currentToken else 'None') )

    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) )

    return currentToken
 
  {% for nonterminal in LL1Nonterminals %}

  def parse_{{nonterminal.string.lower()}}(self):
    current = self.tokens.current()
    rule = self.table[{{nonterminal.id - len(nonAbstractTerminals)}}][current.getId()] if current else -1
    tree = ParseTree( NonTerminal({{nonterminal.id}}, self.nonterminals[{{nonterminal.id}}]))

      {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist'
      {% elif isinstance(nonterminal.macro, NonterminalListMacro) %}
    tree.list = 'nlist'
      {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist'
      {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist'
      {% else %}
    tree.list = False
      {% endif %}

      {% if nonterminal.empty %}
    if current != None and (current.getId() in [{{', '.join([str(a.id) for a in grammar.follow[nonterminal]])}}]):
      return tree
      {% endif %}

    if current == None:
      {% if nonterminal.empty or grammar._empty in grammar.first[nonterminal] %}
      return tree
      {% else %}
      raise SyntaxError('Error: unexpected end of file')
      {% endif %}
    
      {% for index, rule in enumerate(nonterminal.rules) %}

        {% if index == 0 %}
    if rule == {{rule.id}}:
        {% else %}
    elif rule == {{rule.id}}:
        {% endif %}

        {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% elif isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
        {% else %}
      tree.astTransform = AstTransformSubstitution(0)
        {% endif %}

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
      t = self.expect({{morpheme.id}}) # {{morpheme.string}}
      tree.add(t)
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
      tree.listSeparator = t
            {% endif %}
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
      subtree = self.parse_{{morpheme.string.lower()}}()
      tree.add( subtree )
          {% endif %}

        {% endfor %}

      return tree

      {% endfor %}

      {% for exprGrammar in grammar.exprgrammars %}
        {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
          {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}

    elif current.getId() in [{{', '.join([str(x.id) for x in grammar.first[exprGrammar.nonterminal]])}}]:
          {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
          {% elif isinstance(rule.ast, AstSpecification) %}
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', {{rule.ast.parameters}})
          {% else %}
      tree.astTransform = AstTransformSubstitution(0)
          {% endif %}

          {% for morpheme in rule.production.morphemes %}

            {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) ) # {{morpheme.string}}
            {% endif %}

            {% if isinstance(morpheme, NonTerminal) %}
      subtree = self.parse_{{morpheme.string.lower()}}()
      tree.add( subtree )
            {% endif %}
          {% endfor %}
        {% endif %}
      {% endfor %}

      {% if not nonterminal.empty %}
    raise SyntaxError('Error: Unexpected symbol (%s) when parsing %s' % (current, whoami()))
      {% else %}
    return tree
      {% endif %}

  {% endfor %}

  {% for exprGrammar in grammar.exprgrammars %}
  def parse_{{exprGrammar.nonterminal.string.lower()}}( self, rbp = 0):
    name = '{{exprGrammar.nonterminal.string.lower()}}'
    if name not in self.expressionParsers:
      self.expressionParsers[name] = {{prefix}}ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}(self)
    return self.expressionParsers[name].parse(rbp)
  {% endfor %}
