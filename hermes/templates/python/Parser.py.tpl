import sys
import inspect
from collections import OrderedDict
from ..Common import *

{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator %}
{% from hermes.Macro import SeparatedListMacro, MorphemeListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro, OptionallyTerminatedListMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

terminals = {
{% for terminal in grammar.standard_terminals %}
    {{terminal.id}}: '{{terminal.string}}',
{% endfor %}

{% for terminal in grammar.standard_terminals %}
    '{{terminal.string.lower()}}': {{terminal.id}},
{% endfor %}
}

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

nonterminal_first = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.first(nonterminal)])}}],
{% endfor %}
}

nonterminal_follow = {
{% for nonterminal in grammar.nonterminals %}
    {{nonterminal.id}}: [{{', '.join([str(t.id) for t in grammar.follow(nonterminal)])}}],
{% endfor %}
}

rule_first = {
{% for rule in grammar.get_expanded_rules() %}
    {{rule.id}}: [{{', '.join([str(t.id) for t in grammar.first(rule.production)])}}],
{% endfor %}
}

def get_nonterminal_str(id): return nonterminals[id]
def get_terminal_str(id): return terminals[id]
def get_nonterminal_id(str): return nonterminals[str]
def get_terminal_str(str): return terminals[str]
def is_terminal(id): return isinstance(id, int) and id in terminals
def is_nonterminal(id): return isinstance(id, int) and id in nonterminals

def expect(tokens, terminal_id):
    current = tokens.current()
    if not current:
        raise SyntaxError('No more tokens.  Expecting {}'.format(terminals[terminal_id]))
    if current.id != terminal_id:
        raise SyntaxError('Unexpected symbol (line {}, col {}) when parsing {}.  Expected {}, got {}.'.format(
            current.line,
            current.col,
            inspect.stack()[2][3],
            terminals[terminal_id],
            current
        ))

    next = tokens.advance()
    if next and not is_terminal(next.id):
        raise SyntaxError('Invalid symbol ID: {} ({})'.format(next.id, next))

    return current

{% for expression_nonterminal in grammar.expression_nonterminals %}
    {% py name = expression_nonterminal.string %}

# START definitions for expression parser `{{name}}`
{{name}}_infix_binding_power = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
    {% endfor %}
}

{{name}}_prefix_binding_power = {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['unary'] %}
    {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
    {% endfor %}
}

def {{name}}_get_infix_binding_power(terminal_id):
    try:
        return {{name}}_infix_binding_power[terminal_id]
    except:
        return 0

def {{name}}_get_infix_binding_power(terminal_id):
    try:
        return {{name}}_prefix_binding_power[terminal_id]
    except:
        return 0

def {{name}}_parse(tokens, rbp=0):
    left = {{name}}_nud()
    if isinstance(left, ParseTree):
        left.isExpr = True
        left.isNud = True
    while tokens.current() and rbp < {{name}}_get_infix_binding_power(tokens.current.id):
        left = {{name}}_led(left, tokens)
    if left:
        left.isExpr = True
    return left

def {{name}}_nud(tokens):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = tokens.current()

    if not current:
        return tree

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
    {{'if' if i == 0 else 'elif'}} current.id in rule_first[{{rule.id}}]:
        # {{rule}}
        {% if isinstance(rule.nudAst, AstSpecification) %}
        ast_parameters = OrderedDict([
          {% for k,v in rule.nudAst.parameters.items() %}
          ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{rule.nudAst.name}}', ast_parameters)
        {% elif isinstance(rule.nudAst, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{rule.nudAst.idx}})
        {% endif %}

        tree.nudMorphemeCount = {{len(rule.nud_production)}}

        {% for morpheme in rule.nud_production.morphemes %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect({{morpheme.id}}))
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
        tree.add({{name}}_parse({{name}}_get_prefix_binding_power({{rule.operator.operator.id}})))
        tree.isPrefix = True
            {% else %}
        tree.add(parse_{{rule.nonterminal.string.lower()}}())
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}())
          {% elif isinstance(morpheme, LL1ListMacro) %}
        tree.add(parse_{{morpheme.start_nt.string.lower()}}())
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

def {{name}}_led(left, tokens):
    tree = ParseTree(NonTerminal({{expression_nonterminal.id}}, '{{name}}'))
    current = tokens.current()

    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
      {% py led = rule.ledProduction.morphemes %}
      {% if len(led) %}

    if current.id == {{led[0].id}}: # {{led[0]}}

        {% if isinstance(rule.ast, AstSpecification) %}
        ast_parameters = OrderedDict([
          {% for k,v in rule.ast.parameters.items() %}
            ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
          {% endfor %}
        ])
        tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters)
        {% elif isinstance(rule.ast, AstTranslation) %}
        tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
        {% endif %}

        {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
          {% py nt = rule.nud_production.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
        tree.isExprNud = True
          {% endif %}
        {% endif %}

        tree.add(left)

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
        {% for morpheme in led %}
          {% if isinstance(morpheme, Terminal) %}
        tree.add(expect({{morpheme.id}})) # {{morpheme}}
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
        modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
            {% if isinstance(rule.operator, InfixOperator) %}
        tree.isInfix = True
            {% endif %}
        tree.add({{name}}_parse({{name}}_get_prefix_binding_power({{rule.operator.operator.id}}) - modifier))
          {% elif isinstance(morpheme, NonTerminal) %}
        tree.add(parse_{{morpheme.string.lower()}}())
          {% elif isinstance(morpheme, LL1ListMacro) %}
        tree.add(parse_{{morpheme.start_nt.string.lower()}}())
          {% endif %}
        {% endfor %}
      {% endif %}
    {% endfor %}

    return tree

# END definitions for expression parser `{{name}}`
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}
  {% py name = nonterminal.string %}
def parse_{{name}}(tokens):
  current = tokens.current()
  rule = table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.id] if current else -1
  tree = ParseTree(NonTerminal({{nonterminal.id}}, '{{name}}'))

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
  tree.list = 'slist'
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
  tree.list = 'nlist'
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
  tree.list = 'tlist'
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
  tree.list = 'mlist'
    {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
  tree.list = 'otlist'
    {% else %}
  tree.list = False
    {% endif %}

    {% if not grammar.must_consume_tokens(nonterminal) %}
  if current != None and current.id in nonterminal_follow({{nonterminal.id}}) and current.id not in nonterminal_first({{nonterminal.id}}):
      return tree
    {% endif %}

  if current == None:
    {% if grammar.must_consume_tokens(nonterminal) %}
    raise SyntaxError('Error: unexpected end of file')
    {% else %}
    return tree
    {% endif %}

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

      {% if index == 0 %}
  if rule == {{rule.id}}: # {{rule}}
      {% else %}
  elif rule == {{rule.id}}: # {{rule}}
      {% endif %}

      {% if isinstance(rule.ast, AstTranslation) %}
    tree.astTransform = AstTransformSubstitution({{rule.ast.idx}})
      {% elif isinstance(rule.ast, AstSpecification) %}
    ast_parameters = OrderedDict([
        {% for k,v in rule.ast.parameters.items() %}
      ('{{k}}', {% if v == '$' %}'{{v}}'{% else %}{{v}}{% endif %}),
        {% endfor %}
    ])
    tree.astTransform = AstTransformNodeCreator('{{rule.ast.name}}', ast_parameters)
      {% else %}
    tree.astTransform = AstTransformSubstitution(0)
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
    t = expect(tokens, {{morpheme.id}}) # {{morpheme}}
    tree.add(t)
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
    tree.listSeparator = t
            {% endif %}
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
    subtree = parse_{{morpheme.string.lower()}}(tokens)
    tree.add(subtree)
        {% endif %}

      {% endfor %}
    return tree
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
  raise SyntaxError('Error: Unexpected symbol ({}) on line {}, column {} when parsing {}'.format(
    current,
    current.line,
    current.col,
    inspect.stack()[1][3]
  ))
    {% else %}
  return tree
    {% endif %}

{% endfor %}
####
# OLD
####

def parse(tokens):
  return Parser().parse(tokens)

{% for expression_nonterminal in grammar.expression_nonterminals %}
class ExpressionParser_{{expression_nonterminal.string.lower()}}:
  def __init__(self, parent):
    self.__dict__.update(locals())

    self.infixBp = {
      {% for rule in grammar.get_rules(expression_nonterminal) %}
        {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
      {{rule.operator.operator.id}}: {{rule.operator.binding_power}}, # {{rule}}
        {% endif %}
      {% endfor %}
    }

    self.prefixBp = {
      {% for rule in grammar.get_rules(expression_nonterminal) %}
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
    tree = ParseTree( NonTerminal({{expression_nonterminal.id}}, '{{expression_nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    if not current:
      return tree

    {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
      {% py first_set = grammar.first(rule.production) %}
      {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal))%}
    {{'if' if i == 0 else 'elif'}} current.getId() in [{{', '.join(map(str, sorted([x.id for x in first_set])))}}]:
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

      tree.nudMorphemeCount = {{len(rule.nud_production)}}

        {% for morpheme in rule.nud_production.morphemes %}
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
    tree = ParseTree( NonTerminal({{expression_nonterminal.id}}, '{{expression_nonterminal.string.lower()}}') )
    current = self.getCurrentToken()

    {% py seen = list() %}
    {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
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

        {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
          {% py nt = rule.nud_production.morphemes[0] %}
          {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
      tree.isExprNud = True
          {% endif %}
        {% endif %}

      tree.add(left)

        {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
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

  def __init__(self, tokens=None):
    self.__dict__.update(locals())
    self.expressionParsers = dict()

  def isTerminal(self, id):
    return 0 <= id <= {{len(grammar.standard_terminals) - 1}}

  def isNonTerminal(self, id):
    return {{len(grammar.standard_terminals)}} <= id <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}}

  def parse(self, tokens):
    self.tokens = tokens
    tree = self.parse_{{grammar.start.string.lower()}}()
    if self.tokens.current() != None:
      raise SyntaxError('Finished parsing without consuming all tokens.')
    return tree

  def expect(self, terminalId):
    currentToken = self.tokens.current()
    if not currentToken:
      raise SyntaxError('No more tokens.  Expecting {}'.format(self.terminals[terminalId]) )
    if currentToken.getId() != terminalId:
      raise SyntaxError('Unexpected symbol (line {}, col {}) when parsing {}.  Expected {}, got {}.'.format(
        currentToken.line,
        currentToken.col,
        inspect.stack()[2][3],
        self.terminals[terminalId],
        currentToken
      ))

    nextToken = self.tokens.advance()
    if nextToken and not self.isTerminal(nextToken.getId()):
      raise SyntaxError('Invalid symbol ID: {} ({})'.format(nextToken.getId(), nextToken))

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
      {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
    tree.list = 'otlist'
      {% else %}
    tree.list = False
      {% endif %}

      {% if not grammar.must_consume_tokens(nonterminal) %}
    if current != None and \
       (current.getId() in [{{', '.join([str(a.id) for a in grammar.follow(nonterminal)])}}]) and \
       (current.getId() not in [{{', '.join([str(a.id) for a in grammar.first(nonterminal)])}}]):
      return tree
      {% endif %}

    if current == None:
      {% if grammar.must_consume_tokens(nonterminal) %}
      raise SyntaxError('Error: unexpected end of file')
      {% else %}
      return tree
      {% endif %}

      {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}

        {% if index == 0 %}
    if rule == {{rule.id}}: # {{rule}}
        {% else %}
    elif rule == {{rule.id}}: # {{rule}}
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
      t = self.expect({{morpheme.id}}) # {{morpheme}}
      tree.add(t)
            {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
              {% if nonterminal.macro.separator == morpheme %}
      tree.listSeparator = t
              {% endif %}
            {% endif %}
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
      subtree = self.parse_{{morpheme.string.lower()}}()
      tree.add( subtree )
          {% endif %}

        {% endfor %}

      return tree

      {% endfor %}

      {% if grammar.must_consume_tokens(nonterminal) %}
    raise SyntaxError('Error: Unexpected symbol ({}) on line {}, column {} when parsing {}'.format(
      current,
      current.line,
      current.col,
      inspect.stack()[1][3]
    ))
      {% else %}
    return tree
      {% endif %}

  {% endfor %}

  {% for expression_nonterminal in grammar.expression_nonterminals %}
  def parse_{{expression_nonterminal.string.lower()}}(self, rbp = 0):
    name = '{{expression_nonterminal.string.lower()}}'
    if name not in self.expressionParsers:
      self.expressionParsers[name] = ExpressionParser_{{expression_nonterminal.string.lower()}}(self)
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
