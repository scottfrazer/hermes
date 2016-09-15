package main // TODO

{% if len(header)%}
{{'\n'.join(['// ' + s for s in header.split('\n')])}}
{% endif %}

import (
  "fmt"
  "regexp"
  "encoding/base64"
	"errors"
	"strings"
	{% if add_main %}
	"os"
	"io/ioutil"
	{% endif %}
)

{% import re %}
{% from hermes.grammar import * %}

type terminal struct {
  id int
  idStr string
}

type nonTerminal struct {
  id int
  idStr string
  firstSet []int
  followSet []int
  rules[]int
}

func (nt *nonTerminal) CanStartWith(terminalId int) bool {
  for i := range nt.firstSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

func (nt *nonTerminal) CanBeFollowedBy(terminalId int) bool {
  for i := range nt.followSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

type rule struct {
  id int
  str string
  firstSet []int
}

func (rule *rule) CanStartWith(terminalId int) bool {
  for i := range rule.firstSet {
    if i == terminalId {
      return true
    }
  }
  return false
}

type Token struct {
  terminal *terminal
  sourceString string
  resource string
  line int
  col int
}

func (t *Token) String() string {
  return fmt.Sprintf(`<%s:%d:%d %s "%s">`, t.resource, t.line, t.col, t.terminal.idStr, base64.StdEncoding.EncodeToString([]byte(t.sourceString)))
}

func (t *Token) PrettyString() string {
  return t.String()
}

func (t *Token) Ast() AstNode {
  return t
}

type TokenStream struct {
  tokens []*Token
  index int
}

func (ts *TokenStream) current() *Token {
  if ts.index < len(ts.tokens) {
    return ts.tokens[ts.index]
  }
  return nil
}

func (ts *TokenStream) advance() *Token {
  ts.index = ts.index + 1
  return ts.current()
}

func (ts *TokenStream) last() *Token {
  if len(ts.tokens) > 0 {
    return ts.tokens[len(ts.tokens)-1]
  }
  return nil
}

type parseTree struct {
  nonterminal *nonTerminal
  children []treeNode
  astTransform interface{}
  isExpr bool
  isNud bool
  isPrefix bool
  isInfix bool
  nudMorphemeCount int
  isExprNud bool // true for rules like _expr := {_expr} + {...}
  list_separator_id int
  list bool
}

type treeNode interface {
	String() string
	PrettyString() string
	Ast() AstNode
}

func (tree *parseTree) Add(node interface{}) error {
	switch t := node.(type) {
	case *parseTree:
		tree.children = append(tree.children, t)
	case *Token:
		tree.children = append(tree.children, t)
	default:
		return errors.New("only *parseTree and *Token allowed to be added")
	}
	return nil
}

func (tree *parseTree) isCompoundNud() bool{
	if ( len(tree.children) > 0) {
		switch firstChild := tree.children[0].(type) {
		case *parseTree:
			return firstChild.isNud && !firstChild.isPrefix && !firstChild.isExprNud && !firstChild.isInfix
		}
	}
	return false
}

func (tree *parseTree) Ast() AstNode {
    if tree.list == true {
			r := AstList{}
			if len(tree.children) == 0 {
				return &r
			}
			for _, child := range tree.children {
				switch t := child.(type) {
				case *Token:
					if tree.list_separator_id == t.terminal.id {
						continue
					}
					r = append(r, t.Ast())
				default:
					r = append(r, t.Ast())
				}
			}
			return &r
    } else if tree.isExpr {
			switch transform := tree.astTransform.(type) {
			case *AstTransformSubstitution:
				return tree.children[*transform].Ast()
			case *AstTransformNodeCreator:
				attributes := make(map[string]AstNode)
				var child treeNode
				var firstChild interface{}
				if len(tree.children) > 0 {
					firstChild = tree.children[0]
				}
				_, is_tree := firstChild.(*parseTree)
				for s, i := range transform.parameters {
					if i == '$' {
							child = tree.children[0]
					} else if tree.isCompoundNud() {
							firstChild := tree.children[0].(*parseTree)

							if ( i < firstChild.nudMorphemeCount ) {
									child = firstChild.children[i]
							} else {
									i = i - firstChild.nudMorphemeCount + 1
									child = tree.children[i]
							}
					} else if ( len(tree.children) == 1 && !is_tree ) {
							// TODO: I don't think this should ever be called
							fmt.Println("!!!!! THIS CODE ACTUALLY IS CALLED")
							child = tree.children[0]
					} else {
							child = tree.children[i];
					}
					attributes[s] = child.Ast();
				}
				return &Ast{transform.name, attributes}
			}
    } else {
			switch transform := tree.astTransform.(type) {
			case *AstTransformSubstitution:
				return tree.children[*transform].Ast()
			case *AstTransformNodeCreator:
				attributes := make(map[string]AstNode)
				for s, i := range transform.parameters {
					attributes[s] = tree.children[i].Ast()
				}
				return &Ast{transform.name, attributes}
			}

			if len(tree.children) > 0 {
				return tree.children[0].Ast()
			}
    }
	return nil
}

func (tree *parseTree) String() string {
  return parseTreeToString(tree, 0, 1)
}

func (tree *parseTree) PrettyString() string {
  return parseTreeToString(tree, 2, 1)
}

func parseTreeToString(treenode interface{}, indent int, indentLevel int) string {
	indentStr := ""
	if indent > 0 {
		indentStr = strings.Repeat(" ", indent * indentLevel)
	}

	switch node := treenode.(type) {
	case *parseTree:
		childStrings := make([]string, len(node.children))
		for index, child := range node.children {
			childStrings[index] = parseTreeToString(child, indent, indentLevel+1)
		}
		if indent == 0 || len(node.children) == 0 {
			return fmt.Sprintf("%s(%s: %s)", indentStr, node.nonterminal.idStr, strings.Join(childStrings, ", "))
		} else {
			return fmt.Sprintf("%s(%s:\n%s\n%s)", indentStr, node.nonterminal.idStr, strings.Join(childStrings, ",\n"), indentStr)
		}
	case *Token:
		return fmt.Sprintf("%s%s", indentStr, node.String())
	default:
		panic(fmt.Sprintf("parseTreeToString() called on %t", node))
	}
}

type AstNode interface {
	String() string
	PrettyString() string
}

type Ast struct {
  name string
  attributes map[string]AstNode
}

func (ast *Ast) String() string {
  return astToString(ast, 0, 0)
}

func (ast *Ast) PrettyString() string {
  return astToString(ast, 2, 0)
}

func astToString(ast interface{}, indent int, indentLevel int) string {
		indentStr := ""
		nextIndentStr := ""
		attrPrefix := ""

		if indent > 0 {
			indentStr = strings.Repeat(" ", indent * indentLevel)
			nextIndentStr = strings.Repeat(" ", indent * (indentLevel+1))
			attrPrefix = nextIndentStr
		}

		switch node := ast.(type) {
		case *Ast:
			childStrings := make([]string, len(node.attributes))
			for name, subnode := range node.attributes {
				childString := fmt.Sprintf("%s%s=%s", attrPrefix, name, astToString(subnode, indent, indentLevel+1))
				childStrings = append(childStrings, childString)
			}
			if indent > 0 {
				return fmt.Sprintf("(%s:\n%s\n%s)", node.name, strings.Join(childStrings, ",\n"), indentStr)
			} else {
				return fmt.Sprintf("(%s: %s)", node.name, strings.Join(childStrings, ", "))
			}
		case *AstList:
			childStrings := make([]string, len(*node))
			for subnode := range *node {
				childString := fmt.Sprintf("%s%s", attrPrefix, astToString(subnode, indent, indentLevel+1))
				childStrings = append(childStrings, childString)
			}

			if indent == 0 || len(*node) == 0 {
					return fmt.Sprintf("[%s]", strings.Join(childStrings, ", "))
			} else {
					return fmt.Sprintf("[\n%s\n%s]", indentStr, strings.Join(childStrings, ",\n"))
			}
		case *Token:
			return node.String()
		default:
			panic(fmt.Sprintf("Wrong type to astToString(): %v (%t)", ast, ast))
		}
	return ""
}

type AstTransformSubstitution int

func (t *AstTransformSubstitution) String() string {
  return fmt.Sprintf("$%d", *t)
}

type AstTransformNodeCreator struct {
  name string
  parameters map[string]int // TODO: I think this is the right type?
}

func (t *AstTransformNodeCreator) String() string {
	strs := make([]string, len(t.parameters))
	for k, v := range t.parameters {
		strs = append(strs, fmt.Sprintf("%s=$%d", k, v))
	}

	return fmt.Sprintf("%s(%s)", t.name, strings.Join(strs, ", "))
}


type AstList []AstNode

func (ast *AstList) String() string {
  return astToString(ast, 0, 0)
}

func (ast *AstList) PrettyString() string {
  return astToString(ast, 2, 0)
}

type SyntaxError struct {
  message string
}

func (err *SyntaxError) Error() string {
	return err.message
}

type SyntaxErrors []*SyntaxError

func (errs SyntaxErrors) Error() string {
	strs := make([]string, len(errs))
	for _, e := range errs {
		strs = append(strs, e.Error())
	}
	return strings.Join(strs, strings.Repeat("=", 50))
}

type SyntaxErrorHandler interface {
	unexpected_eof() *SyntaxError
	excess_tokens() *SyntaxError
	unexpected_symbol(nt string, actual_token *Token, expected_terminals []*terminal, rule string) *SyntaxError
  no_more_tokens(nt string, expected_terminal *terminal, last_token *Token) *SyntaxError
	invalid_terminal(nt string, invalid_token *Token) *SyntaxError
	unrecognized_token(s string, line, col int) *SyntaxError
	missing_list_items(method string , required, found int, last string) *SyntaxError
	missing_terminator(method string, required *terminal, terminator *terminal, last *terminal) *SyntaxError
	Error() string
}

type DefaultSyntaxErrorHandler struct {
  syntaxErrors SyntaxErrors
}

func (h *DefaultSyntaxErrorHandler) Error() string {
	return h.syntaxErrors.Error()
}

func (h *DefaultSyntaxErrorHandler) _error(str string) *SyntaxError{
	e := &SyntaxError{str}
	h.syntaxErrors = append(h.syntaxErrors, e)
	return e
}
func (h *DefaultSyntaxErrorHandler) unexpected_eof() *SyntaxError {
    return h._error("Error: unexpected end of file")
}
func (h *DefaultSyntaxErrorHandler) excess_tokens() *SyntaxError {
    return h._error("Finished parsing without consuming all tokens.")
}
func (h *DefaultSyntaxErrorHandler) unexpected_symbol(nt string, actual_token *Token, expected_terminals []*terminal, rule string) *SyntaxError {
	strs := make([]string, len(expected_terminals))
	for _, t := range expected_terminals {
		strs = append(strs, t.idStr)
	}
	return h._error(fmt.Sprintf("Unexpected symbol (line %d, col %d) when parsing parse_%s.  Expected %s, got %s.",
			actual_token.line,
			actual_token.col,
			nt,
			strings.Join(strs, ", "),
			actual_token.terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) no_more_tokens(nt string, expected_terminal *terminal, last_token *Token) *SyntaxError {
    return h._error(fmt.Sprintf("No more tokens.  Expecting %s", expected_terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) invalid_terminal(nt string, invalid_token *Token) *SyntaxError {
    return h._error(fmt.Sprintf("Invalid symbol ID: %d (%s)", invalid_token.terminal.id, invalid_token.terminal.idStr))
}
func (h *DefaultSyntaxErrorHandler) unrecognized_token(s string, line, col int) *SyntaxError {
	lines := strings.Split(s, "\n")
	bad_line := lines[line-1]
	return h._error(fmt.Sprintf("Unrecognized token on line %d, column %d:\n\n%s\n%s",
		 line, col, bad_line, strings.Repeat(" ", col-1) + "^"))
}
func (h *DefaultSyntaxErrorHandler) missing_list_items(method string , required, found int, last string) *SyntaxError {
	return h._error(fmt.Sprintf("List for %s requires %d items but only %d were found.", method, required, found))
}
func (h *DefaultSyntaxErrorHandler) missing_terminator(method string, required *terminal, terminator *terminal, last *terminal) *SyntaxError {
	return h._error(fmt.Sprintf("List for %s is missing a terminator", method))
}

/*
 * Parser Code
 */

var table [][]int
var terminals []*terminal
var nonterminals []*nonTerminal
var rules []*rule

func initTable() [][]int {
  if table == nil {
    table = make([][]int, {{len(grammar.nonterminals)}})
{% py parse_table = grammar.parse_table %}
{% for i in range(len(grammar.nonterminals)) %}
    table[{{i}}] = []int{ {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} }
{% endfor %}
  }
  return table
}

func initTerminals() []*terminal {
  if terminals == nil {
    terminals = make([]*terminal, {{len(grammar.standard_terminals)}})
{% for index, terminal in enumerate(grammar.standard_terminals) %}
    terminals[{{index}}] = &terminal{ {{terminal.id}}, "{{terminal.string}}" }
{% endfor %}
  }
  return terminals
}

func initNonTerminals() []*nonTerminal {
  if nonterminals == nil {
    nonterminals = make([]*nonTerminal, {{len(grammar.nonterminals)}})
    var first []int
    var follow []int
		var rules []int
{% for index, nt in enumerate(grammar.nonterminals) %}
    first = []int{ {{', '.join([str(t.id) for t in grammar.first(nt)])}} }
    follow = []int{ {{', '.join([str(t.id) for t in grammar.follow(nt)])}} }
    {% py nt_rules = [rule for rule in grammar.get_expanded_rules(nt)] %}
    rules = []int { {{ ', '.join([str(r.id) for r in nt_rules]) }} }
    nonterminals[{{index}}] = &nonTerminal{ {{nt.id}}, "{{nt.string}}", first, follow, rules }
{% endfor %}
  }
  return nonterminals
}

func initRules() []*rule {
  if rules == nil {
{% py rules = grammar.get_expanded_rules() %}
    rules = make([]*rule, {{len(rules)}})
    var firstSet []int
{% for index, rule in enumerate(rules) %}
    firstSet = []int{ {{', '.join([str(t.id) for t in grammar.first(rule.production)])}} }
    rules[{{index}}] = &rule{ {{rule.id}}, "{{rule}}", firstSet }
{% endfor %}
  }
  return rules
}

type ParserContext struct {
  tokens *TokenStream
  errors SyntaxErrorHandler
  nonterminal_string string
  rule_string string
}

func (ctx *ParserContext) expect(terminal_id int) (*Token, error) {
    current := ctx.tokens.current()
    if current == nil {
        err := ctx.errors.no_more_tokens(ctx.nonterminal_string, terminals[terminal_id], ctx.tokens.last())
        return nil, err
    }
    if current.terminal.id != terminal_id {
				expected := make([]*terminal, 1)
				expected[0] = initTerminals()[terminal_id] // TODO: don't use initTerminals here
        err := ctx.errors.unexpected_symbol(ctx.nonterminal_string, current, expected, ctx.rule_string)
        return nil, err
    }
    next := ctx.tokens.advance()
    if next != nil && !ctx.IsValidTerminalId(next.terminal.id) {
        err := ctx.errors.invalid_terminal(ctx.nonterminal_string, next)
        return nil, err
    }
    return current, nil
}

type {{ccPrefix}}Parser struct {
  table [][]int
  terminals []*terminal
  nonterminals []*nonTerminal
  rules []*rule
}

func New{{ccPrefix}}Parser() *{{ccPrefix}}Parser {
  return &{{ccPrefix}}Parser{
    initTable(),
    initTerminals(),
    initNonTerminals(),
    initRules()}
}

func (parser *{{ccPrefix}}Parser) newParseTree(nonterminalId int) *parseTree {
	var nt *nonTerminal
	for _, n := range parser.nonterminals {
		if n.id == nonterminalId {
			nt = n
		}
	}
	return &parseTree{
		nonterminal: nt,
  	children: nil,
		astTransform: nil,
		isExpr: false,
		isNud: false,
		isPrefix: false,
		isInfix: false,
  	nudMorphemeCount: 0,
		isExprNud: false,
		list_separator_id: -1,
		list: false}
}

func (parser *{{ccPrefix}}Parser) ParseTokens(stream *TokenStream, handler SyntaxErrorHandler) (*parseTree, error) {
  ctx := ParserContext{stream, handler, "", ""}
  tree, err := parser.Parse_{{grammar.start.string.lower()}}(&ctx)
	if err != nil {
		return nil, err
	}
  if stream.current() != nil {
    ctx.errors.excess_tokens()
    return nil, ctx.errors
  }
  return tree, nil
}

func (parser *{{ccPrefix}}Parser) TerminalFromId(id int) *terminal {
  return parser.terminals[id]
}

func (parser *{{ccPrefix}}Parser) NonTerminalFromId(id int) *nonTerminal {
  return parser.nonterminals[{{len(grammar.standard_terminals)}} - id]
}

func (parser *{{ccPrefix}}Parser) TerminalFromStringId(id string) *terminal {
  for _, t := range parser.terminals {
    if t.idStr == id {
      return t
    }
  }
  return nil;
}

func (parser *{{ccPrefix}}Parser) Rule(id int) *rule {
  for _, r := range parser.rules {
    if r.id == id {
      return r
    }
  }
  return nil;
}

func (ctx *ParserContext) IsValidTerminalId(id int) bool {
  return 0 <= id && id <= {{len(grammar.standard_terminals) - 1}}
}

{% for expression_nonterminal in sorted(grammar.expression_nonterminals, key=str) %}
    {% py name = expression_nonterminal.string %}

func (parser *{{ccPrefix}}Parser) infixBindingPower_{{name}}(terminal_id int) int {
  switch terminal_id {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
      {% if rule.operator and rule.operator.associativity in ['left', 'right'] %}
  case {{rule.operator.operator.id}}: return {{rule.operator.binding_power}} // {{rule}}
      {% endif %}
    {% endfor %}
  }
	return 0
}

func (parser *{{ccPrefix}}Parser) prefixBindingPower_{{name}}(terminal_id int) int {
  switch terminal_id {
    {% for rule in grammar.get_rules(expression_nonterminal) %}
      {% if rule.operator and rule.operator.associativity in ['unary'] %}
  case {{rule.operator.operator.id}}: return {{rule.operator.binding_power}} // {{rule}}
      {% endif %}
    {% endfor %}
  }
	return 0
}

func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx *ParserContext) (*parseTree, error) {
    return parser._parse_{{name}}(ctx, 0)
}

func (parser *{{ccPrefix}}Parser) _parse_{{name}}(ctx *ParserContext, rbp int) (*parseTree, error) {
    left, err := parser.nud_{{name}}(ctx)
		if err != nil {
			return nil, err
		}
		if left != nil {
			left.isExpr = true
			left.isNud = true
		}
    for ctx.tokens.current() != nil && rbp < parser.infixBindingPower_{{name}}(ctx.tokens.current().terminal.id) {
      left, err = parser.led_{{name}}(left, ctx)
			if err != nil {
				return nil, err
			}
    }
    if left != nil {
      left.isExpr = true
    }
    return left, nil
}

func (parser *{{ccPrefix}}Parser) nud_{{name}}(ctx *ParserContext) (*parseTree, error) {
	tree := parser.newParseTree({{expression_nonterminal.id}})
	current := ctx.tokens.current()
  ctx.nonterminal_string = "{{name}}"

  if current == nil {
    return tree, nil
  }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py first_set = grammar.first(rule.production) %}
    {% if len(first_set) and not first_set.issuperset(grammar.first(expression_nonterminal)) %}
  if parser.Rule({{rule.id}}).CanStartWith(current.terminal.id) {
      ctx.rule_string = parser.Rule({{rule.id}}).str

      {% py ast = rule.nudAst if not isinstance(rule.operator, PrefixOperator) else rule.ast %}

      {% if isinstance(ast, AstSpecification) %}
			astParameters := make(map[string]int)
        {% for k,v in ast.parameters.items() %}
      astParameters["{{k}}"] = {% if v == '$' %}int('{{v}}'){% else %}{{v}}{% endif %}
        {% endfor %}
      tree.astTransform = &AstTransformNodeCreator{"{{ast.name}}", astParameters}
      {% elif isinstance(ast, AstTranslation) %}
      tree.astTransform = {{ast.idx}}
      {% endif %}

      tree.nudMorphemeCount = {{len(rule.nud_production)}}

      {% for morpheme in rule.nud_production.morphemes %}
        {% if isinstance(morpheme, Terminal) %}
      token, err := ctx.expect({{morpheme.id}})
      if err != nil {
        return nil, err
      }
      tree.Add(token)
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
          {% if isinstance(rule.operator, PrefixOperator) %}
      subtree, err := parser._parse_{{name}}(ctx, parser.prefixBindingPower_{{name}}({{rule.operator.operator.id}}))
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
      tree.isPrefix = true
          {% else %}
      subtree, err := parser.Parse_{{rule.nonterminal.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
          {% endif %}
        {% elif isinstance(morpheme, NonTerminal) %}
      subtree, err := parser.Parse_{{morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
        {% endif %}
      {% endfor %}
  }
    {% endif %}
  {% endfor %}

  return tree, nil
}

func (parser *{{ccPrefix}}Parser) led_{{name}}(left *parseTree, ctx *ParserContext) (*parseTree, error) {
	tree := parser.newParseTree({{expression_nonterminal.id}})
	current := ctx.tokens.current()
  ctx.nonterminal_string = "{{name}}"

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.led_production.morphemes %}
    {% if len(led) %}

  if current.terminal.id == {{led[0].id}} {
      // {{rule}}
      ctx.rule_string = parser.Rule({{rule.id}}).str

      {% if isinstance(rule.ast, AstSpecification) %}
      var astParameters = make(map[string]int)
        {% for k,v in rule.ast.parameters.items() %}
      astParameters["{{k}}"] = {% if v == '$' %}int('{{v}}'){% else %}{{v}}{% endif %}
        {% endfor %}
      tree.astTransform = &AstTransformNodeCreator{"{{rule.ast.name}}", astParameters}
      {% elif isinstance(rule.ast, AstTranslation) %}
      tree.astTransform = {{rule.ast.idx}}
      {% endif %}

      {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
        {% py nt = rule.nud_production.morphemes[0] %}
        {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
      tree.isExprNud = true
        {% endif %}
      {% endif %}

      tree.Add(left)

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
      {% for morpheme in led %}
        {% if isinstance(morpheme, Terminal) %}
      token, err := ctx.expect({{morpheme.id}}) // {{morpheme}}
      if err != nil {
        return nil, err
      }
      tree.Add(token)
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
      modifier := {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}}
          {% if isinstance(rule.operator, InfixOperator) %}
      tree.isInfix = true
          {% endif %}
      subtree, err := parser._parse_{{name}}(ctx, parser.infixBindingPower_{{name}}({{rule.operator.operator.id}}) - modifier)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
        {% elif isinstance(morpheme, NonTerminal) %}
      subtree, err := parser.parse_{{morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
        {% endif %}
      {% endfor %}
	}
    {% endif %}
  {% endfor %}

  return tree, nil
}

{% endfor %}

{% for list_nonterminal in sorted(grammar.list_nonterminals, key=str) %}
  {% py list_parser = grammar.list_parser(list_nonterminal) %}
  {% py name = list_nonterminal.string %}
func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx *ParserContext) (*parseTree, error) {
		current := ctx.tokens.current()
		tree := parser.newParseTree({{list_nonterminal.id}})
    tree.list = true
  {% if list_parser.separator is not None %}
    tree.list_separator_id = {{list_parser.separator.id}}
  {% endif %}
    ctx.nonterminal_string = "{{name}}"

  {% if not grammar.must_consume_tokens(list_nonterminal) %}
		list_nonterminal := parser.NonTerminalFromId({{list_nonterminal.id}})
    if current != nil && list_nonterminal.CanBeFollowedBy(current.terminal.id) && list_nonterminal.CanStartWith(current.terminal.id) {
      return tree, nil
    }
  {% endif %}

    if current == nil {
  {% if grammar.must_consume_tokens(list_nonterminal) %}
      return nil, ctx.error_formatter.unexpected_eof()
  {% else %}
      return tree, nil
  {% endif %}
    }

    minimum := {{list_parser.minimum}}
    for minimum > 0 || (current != nil && parser.NonTerminalFromId({{list_nonterminal.id}}).CanStartWith(current.terminal.id)) {
  {% if isinstance(list_parser.morpheme, NonTerminal) %}
      subtree, err := parser.Parse_{{list_parser.morpheme.string.lower()}}(ctx)
      if err != nil {
        return nil, err
      }
      tree.Add(subtree)
      ctx.nonterminal_string = "{{name}}" // Horrible -- because parse_* can reset this
  {% else %}
      token, err := ctx.expect({{list_parser.morpheme.id}})
      if err != nil {
        return nil, err
      }
      tree.Add(token)
  {% endif %}

  {% if list_parser.separator is not None %}
      if current != nil && current.terminal.id == {{list_parser.separator.id}} {
        token, err := ctx.expect({{list_parser.separator.id}})
        if err != nil {
          return nil, err
        }
        tree.Add(token)
    {% if list_parser.sep_terminates %}
			} else {
        raise ctx.errors.missing_terminator(
          "{{nonterminal.string.lower()}}",
          "{{list_parser.separator.string.upper()}}",
          None
        )
      }
    {% else %}
			} else {
      {% if list_parser.minimum > 0 %}
        if minimum > 1 {
          raise ctx.errors.missing_list_items(
            "{{list_nonterminal.string.lower()}}",
            {{list_parser.minimum}},
            {{list_parser.minimum}} - minimum + 1,
            None
          )
        }
      {% endif %}
        break
      }
    {% endif %}
  {% endif %}

			if minimum - 1 > 0 {
				minimum = minimum - 1
			} else {
				minimum = 0
			}
    }
    return tree, nil
}
{% endfor %}

{% for nonterminal in sorted(grammar.ll1_nonterminals, key=str) %}
  {% py name = nonterminal.string %}
func (parser *{{ccPrefix}}Parser) Parse_{{name}}(ctx *ParserContext) (*parseTree, error) {
	current := ctx.tokens.current()
	rule := -1
	if current != nil {
		rule = parser.table[{{nonterminal.id - len(grammar.standard_terminals)}}][current.terminal.id]
	}
	tree := parser.newParseTree({{nonterminal.id}})
  ctx.nonterminal_string = "{{name}}"
	var token *Token
	var err error

	_ = token
	_ = err

    {% if not grammar.must_consume_tokens(nonterminal) %}
  nt := parser.NonTerminalFromId({{nonterminal.id}})
  if current != nil && nt.CanBeFollowedBy(current.terminal.id) && nt.CanStartWith(current.terminal.id) {
    return tree, nil
  }
    {% endif %}

  if current == nil {
    {% if grammar.must_consume_tokens(nonterminal) %}
    return nil, ctx.errors.unexpected_eof()
    {% else %}
    return tree, nil
    {% endif %}
  }

    {% for index, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}
  if rule == {{rule.id}} { // {{rule}}
    ctx.rule_string = rules[{{rule.id}}].str

      {% if isinstance(rule.ast, AstTranslation) %}

    tree.astTransform = {{rule.ast.idx}}
      {% elif isinstance(rule.ast, AstSpecification) %}
		astParameters := make(map[string]int)
        {% for k,v in rule.ast.parameters.items() %}
    astParameters["{{k}}"] = {% if v == '$' %}int('{{v}}'){% else %}{{v}}{% endif %}
        {% endfor %}
    tree.astTransform = &AstTransformNodeCreator{ "{{rule.ast.name}}", astParameters }
      {% else %}
    tree.astTransform = 0
      {% endif %}

      {% for index, morpheme in enumerate(rule.production.morphemes) %}

        {% if isinstance(morpheme, Terminal) %}
    token, err = ctx.expect({{morpheme.id}}) // {{morpheme}}
    if err != nil {
      return nil, err
    }
    tree.Add(token)
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
    subtree, err := parser.Parse_{{morpheme.string.lower()}}(ctx)
    if err != nil {
      return nil, err
    }
    tree.Add(subtree)
        {% endif %}

      {% endfor %}
    return tree, nil
  }
    {% endfor %}

    {% if grammar.must_consume_tokens(nonterminal) %}
	nt := parser.NonTerminalFromId({{nonterminal.id}})
	expected := make([]*terminal, len(nt.firstSet))
	for _, terminalId := range nt.firstSet {
		for _, terminal := range parser.terminals {
			if terminal.id == terminalId {
				expected = append(expected, terminal)
				break
			}
		}
	}

  return nil, ctx.errors.unexpected_symbol(
    ctx.nonterminal_string,
    ctx.tokens.current(),
    expected,
    rules[{{rule.id}}].str)
    {% else %}
  return tree, nil
    {% endif %}
}
{% endfor %}

{% if lexer %}

/*
 * Lexer Code
 */

/* START USER CODE */
{{lexer.code}}
/* END USER CODE */

func (ctx *LexerContext) emit(terminal *terminal, sourceString string, line, col int) {
  if terminal != nil {
    ctx.tokens = append(ctx.tokens, &Token{terminal, sourceString, ctx.resource, line, col})
  }
}

{% if re.search(r'func\s+default_action', lexer.code) is None %}
func default_action(ctx *LexerContext, terminal *terminal, sourceString string, line, col int) {
    ctx.emit(terminal, sourceString, line, col)
}
{% endif %}

{% if re.search(r'func\s+lexerInit', lexer.code) is None %}
func lexerInit() interface{} {
    return nil
}
{% endif %}

{% if re.search(r'func\s+lexerDestroy', lexer.code) is None %}
func lexerDestroy(context interface{}) {}
{% endif %}

type LexerContext struct {
  source string
  resource string
  handler SyntaxErrorHandler
  userContext interface{}
  stack []string
  line int
  col int
  tokens []*Token
}

func (ctx *LexerContext) StackPush(mode string) {
  ctx.stack = append(ctx.stack, mode)
}

func (ctx *LexerContext) StackPop() {
  ctx.stack = ctx.stack[:len(ctx.stack)-1]
}

func (ctx *LexerContext) StackPeek() string {
  return ctx.stack[len(ctx.stack)-1]
}

type HermesRegex struct {
  regex *regexp.Regexp
  outputs []HermesLexerAction
}

type HermesLexerAction interface {
  HandleMatch(ctx *LexerContext, groups []string, indexes []int)
}

type LexerRegexOutput struct {
  terminal *terminal
  group int
  function func(*LexerContext, *terminal, string, int, int)
}

func (lro *LexerRegexOutput) HandleMatch(ctx *LexerContext, groups []string, indexes []int) {
  sourceString := ""
  startIndex := 0
  if lro.group > 0 {
    sourceString = groups[lro.group]
    startIndex = lro.group * 2
  }

	groupLine, groupCol := _advance_line_col(ctx.source, indexes[startIndex], ctx.line, ctx.col)

  lro.function(ctx, lro.terminal, sourceString, groupLine, groupCol)
}

type LexerStackPush struct {
  mode string
}

func (lsp *LexerStackPush) HandleMatch(ctx *LexerContext, groups []string, indexes []int) {
  ctx.StackPush(lsp.mode)
}

type LexerAction struct {
  action string
}

func (la *LexerAction) HandleMatch(ctx *LexerContext, groups []string, indexes []int) {
  if la.action == "pop" {
    ctx.StackPop()
  }
}

var regex map[string][]*HermesRegex

func initRegexes() map[string][]*HermesRegex {
  if regex == nil {
    regex = make(map[string][]*HermesRegex)
    var matchActions []HermesLexerAction
    var matchFunction func(*LexerContext, *terminal, string, int, int)
    var r *regexp.Regexp
    var terminals = initTerminals() // TODO: don't require this
    var findTerminal = func(name string) *terminal {
      for _, terminal := range terminals {
        if terminal.idStr == name {
         	return terminal
        }
      }
			return nil
    }

{% for mode, regex_list in lexer.items() %}
    regex["{{mode}}"] = make([]*HermesRegex, {{len(regex_list)}})
  {% for index, regex in enumerate(regex_list) %}
    r = regexp.MustCompile({{regex.regex}})
    // TODO: set r.Flags
    matchActions = make([]HermesLexerAction, {{len(regex.outputs)}})
    {% for index2, output in enumerate(regex.outputs) %}
      {% if isinstance(output, RegexOutput) %}
		matchFunction = {{output.function if output.function is not None else 'default_action'}}
    matchActions[{{index2}}] = &LexerRegexOutput{ findTerminal({{'"' + output.terminal.string.lower() + '"' if output.terminal else '""'}}), {{output.group}}, matchFunction }
      {% elif isinstance(output, LexerStackPush) %}
    matchActions[{{index2}}] = &LexerStackPush{ "{{output.mode}}" }
      {% elif isinstance(output, LexerAction) %}
    matchActions[{{index2}}] = &LexerAction{ "{{output.action}}" }
      {% endif %}
    {% endfor %}
    regex["{{mode}}"][{{index}}] = &HermesRegex{r, matchActions}
  {% endfor %}
{% endfor %}
  }
  return regex
}

type {{ccPrefix}}Lexer struct {
  regex map[string][]*HermesRegex
}

func New{{ccPrefix}}Lexer() *{{ccPrefix}}Lexer {
  return &{{ccPrefix}}Lexer{initRegexes()}
}

func _advance_line_col(s string, length, line, col int) (int, int) {
  c := 0
  for r := range s {
    c += 1
    if r == '\n' {
      line += 1
      col = 1
    } else {
      col += 1
    }
    if c == length {
      break
    }
  }
  return line, col
}

func (lexer *{{ccPrefix}}Lexer) _advance_string(ctx *LexerContext, s string) {
    ctx.line, ctx.col = _advance_line_col(s, len(s), ctx.line, ctx.col)
    ctx.source = ctx.source[len(s):]
}

func (lexer *{{ccPrefix}}Lexer) _next(ctx *LexerContext) bool {
    for _, regex := range lexer.regex[ctx.StackPeek()] {
				groups := regex.regex.FindStringSubmatch(ctx.source)
				indexes := regex.regex.FindStringSubmatchIndex(ctx.source)
        if groups != nil && indexes != nil {
            for _, output := range regex.outputs {
              output.HandleMatch(ctx, groups, indexes)
            }
            lexer._advance_string(ctx, groups[0])
            return len(groups[0]) > 0
        }
    }
    return false
}

func (lexer *{{ccPrefix}}Lexer) lex(source, resource string, handler SyntaxErrorHandler) ([]*Token, error) {
  user_context := lexerInit()
  ctx := &LexerContext{source, resource, handler, lexerInit(), nil, 1, 1, nil}

  for len(ctx.source) > 0 {
    matched := lexer._next(ctx)
    if matched == false {
      return nil, ctx.handler.unrecognized_token(source, ctx.line, ctx.col)
    }
  }

  lexerDestroy(user_context)
  return ctx.tokens, nil
}

func (lexer *{{ccPrefix}}Lexer) Lex(source, resource string, handler SyntaxErrorHandler) (*TokenStream, error) {
	tokens, err := lexer.lex(source, resource, handler)
	if err != nil {
		return nil, err
	}
	return &TokenStream{tokens, 0}, nil
}

{% endif %}

{% if add_main %}

/*
 * Main
 */

func main() {
    if len(os.Args) != 3 || (os.Args[1] != "parsetree" && os.Args[1] != "ast"{% if lexer %} && os.Args[1] != "tokens"{% endif %}) {
        fmt.Printf("Usage: %s parsetree <source>\n", os.Args[0])
        fmt.Printf("Usage: %s ast <source>\n", os.Args[0])
        {% if lexer %}
        fmt.Printf("Usage: %s tokens <source>\n", os.Args[0])
        {% endif %}
        os.Exit(-1)
    }

    bytes, err := ioutil.ReadFile(os.Args[2])
    if err != nil {
      fmt.Printf("Error reading file %s: %s", os.Args[2], err)
      os.Exit(-1)
    }

    parser := New{{ccPrefix}}Parser()
		lexer := New{{ccPrefix}}Lexer()
		// TODO: clean up interface for DefaultSyntaxErrorHandler
		handler := &DefaultSyntaxErrorHandler{nil}
		tokens, err := lexer.Lex(string(bytes), os.Args[2], handler)
		if err != nil {
			fmt.Printf("%s\n", err)
			os.Exit(-1)
		}

    if os.Args[1] == "parsetree" || os.Args[1] == "ast" {
      tree, err := parser.ParseTokens(tokens, handler)
			if err != nil {
				fmt.Printf("%s\n", err)
				os.Exit(-1)
			}
      if os.Args[1] == "parsetree" {
        fmt.Println(tree.PrettyString())
      } else {
        ast := tree.Ast()
        if ast != nil {
          fmt.Println(ast.PrettyString())
        }
      }
    }
    if os.Args[1] == "tokens" {
      for _, token := range tokens.tokens {
        fmt.Println(token.PrettyString())
      }
    }
}
{% endif %}
