import sys
import inspect
from collections import OrderedDict
from ..Common import *

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

def whoami():
  return inspect.stack()[1][3]

def whosdaddy():
  return inspect.stack()[2][3]

def parse(tokens):
  return Parser().parse(tokens)

{% for exprGrammar in grammar.exprgrammars %}
class ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}:
  def __init__(self, parent):
    self.__dict__.update(locals())

    self.infixBp = {
      {% for rule in exprGrammar.rules %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
      {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
      {% endfor %}
    }

    self.prefixBp = {
      {% for rule in exprGrammar.rules %}
        {% if rule.operator and rule.operator.associativity in ['unary'] %}
      {{rule.operator.operator.id}}: {{rule.operator.binding_power}},
        {% endif %}
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

    {% for i, rule in enumerate(grammar.grammar_expanded_rules[exprGrammar]) %}
      {% py ruleFirstSet = grammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}
      {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first[exprGrammar.nonterminal])%}
    {{'if' if i == 0 else 'elif'}} current.getId() in [{{', '.join(map(str, sorted([x.id for x in ruleFirstSet])))}}]:
      # {{rule}}
        {% if isinstance(rule.nudAst, AstSpecification) %}
      astParameters = OrderedDict([
          {% for k,v in rule.nudAst.parameters.items() %}
        ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
      ])
      tree.astTransform = AstTransformNodeCreator('{{rule.nudAst.name}}', astParameters)
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
    {% for rule in grammar.grammar_expanded_expr_rules[exprGrammar] %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) and led[0] not in seen %}

    {{'if' if len(seen)==0 else 'else if'}} current.getId() == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
      astParameters = OrderedDict([
          {% for k,v in rule.ast.parameters.items() %}
        ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
      ])
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', astParameters)
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

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in exprGrammar.rules if rule.operator} %}
        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
      tree.add( self.expect({{morpheme.id}}) )
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
      modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
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

class Parser:
  # Quark - finite string set maps one string to exactly one int, and vice versa
  terminals = {
  {% for terminal in grammar.standard_terminals %}
    {{terminal.id}}: '{{terminal.string}}',
  {% endfor %}

  {% for terminal in grammar.standard_terminals %}
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
    {% py parse_table = grammar.parse_table %}
    {% for i in range(len(grammar.nonterminals)) %}
    [{{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}}],
    {% endfor %}
  ]

  {% for terminal in grammar.standard_terminals %}
  TERMINAL_{{terminal.string.upper()}} = {{terminal.id}}
  {% endfor %}

  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()

  def isTerminal(self, id):
    return 0 <= id <= {{len(grammar.standard_terminals) - 1}}

  def isNonTerminal(self, id):
    return {{len(grammar.standard_terminals)}} <= id <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}}

  def parse(self, tokens):
    self.tokens = tokens
    self.start = '{{str(grammar.start).upper()}}'
    tree = self.parse_{{grammar.start.string.lower()}}()
    if self.tokens.current() != None:
      raise SyntaxError( 'Finished parsing without consuming all tokens.' )
    return tree

  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError( 'No more tokens.  Expecting %s' % (self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError( 'Unexpected symbol (line %d, col %d) when parsing %s.  Expected %s, got %s.' %(currentToken.line, currentToken.col, whosdaddy(), self.terminals[terminalId], currentToken) )

    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) )

    return currentToken
 
  {% for nonterminal in grammar.ll1_nonterminals %}

  def parse_{{nonterminal.string.lower()}}(self):
    current = self.tokens.current()
    rule = self.table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.getId()] if current else -1
    tree = ParseTree( NonTerminal({{nonterminal.id}}, self.nonterminals[{{nonterminal.id}}]))

      {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
    tree.list = 'slist'
      {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
    tree.list = 'nlist'
      {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
    tree.list = 'tlist'
      {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
    tree.list = 'mlist'
      {% else %}
    tree.list = False
      {% endif %}

      {% if grammar.must_consume_tokens(nonterminal) %}
    if current != None and \
       (current.getId() in [{{', '.join([str(a.id) for a in grammar.follow[nonterminal]])}}]) and \
       (current.getId() not in [{{', '.join([str(a.id) for a in grammar.first[nonterminal]])}}]):
      return tree
      {% endif %}

    if current == None:
      {% if grammar.must_consume_tokens(nonterminal) or grammar._empty in grammar.first[nonterminal] %}
      return tree
      {% else %}
      raise SyntaxError('Error: unexpected end of file')
      {% endif %}
    
      {% for index, rule in enumerate(grammar.getExpandedLL1Rules(nonterminal)) %}

        {% if index == 0 %}
    if rule == {{rule.id}}:
        {% else %}
    elif rule == {{rule.id}}:
        {% endif %}

        {% if isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% elif isinstance(rule.ast, AstSpecification) %}
      astParameters = OrderedDict([
          {% for k,v in rule.ast.parameters.items() %}
        ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
      ])
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', astParameters)
        {% else %}
      tree.astTransform = AstTransformSubstitution(0)
        {% endif %}

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
      t = self.expect({{morpheme.id}}) # {{morpheme.string}}
      tree.add(t)
            {% if isinstance(nonterminal.macro, SeparatedListMacro) and nonterminal.macro.separator == morpheme %}
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
      astParameters = OrderedDict([
          {% for k,v in rule.ast.parameters.items() %}
        ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
      ])
      tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', astParameters)
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

      {% if not grammar.must_consume_tokens(nonterminal) %}
    raise SyntaxError('Error: Unexpected symbol (%s) on line %d, column %d when parsing %s' % (current, current.line, current.col, whoami()))
      {% else %}
    return tree
      {% endif %}

  {% endfor %}

  {% for exprGrammar in grammar.exprgrammars %}
  def parse_{{exprGrammar.nonterminal.string.lower()}}( self, rbp = 0):
    name = '{{exprGrammar.nonterminal.string.lower()}}'
    if name not in self.expressionParsers:
      self.expressionParsers[name] = ExpressionParser_{{exprGrammar.nonterminal.string.lower()}}(self)
    return self.expressionParsers[name].parse(rbp)
  {% endfor %}

if __name__ == '__main__':
    import argparse
    import json

    cli_parser = argparse.ArgumentParser(description='Grammar Parser')
    cli_parser.add_argument('--color', action='store_true', help="Print output in terminal colors")
    cli_parser.add_argument('--file')
    cli_parser.add_argument('--out', default='ast', choices=['ast', 'parsetree'])
    cli_parser.add_argument('--stdin', action='store_true')
    cli = cli_parser.parse_args()

    if (not cli.file and not cli.stdin) or (cli.file and cli.stdin):
      sys.exit('Either --file=<path> or --stdin required, but not both')

    cli.file = open(cli.file) if cli.file else sys.stdin
    json_tokens = json.loads(cli.file.read())
    cli.file.close()

    tokens = TokenStream() 
    for json_token in json_tokens:
        tokens.append(Terminal(
            Parser.terminals[json_token['terminal']],
            json_token['terminal'],
            json_token['source_string'],
            json_token['resource'],
            json_token['line'],
            json_token['col']
        ))

    try:
        tree = parse(tokens)
        if cli.out == 'parsetree':
          print(ParseTreePrettyPrintable(tree, color=cli.color))
        else:
          print(AstPrettyPrintable(tree.toAst(), color=cli.color))
    except SyntaxError as error:
        print(error)
