{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}

#include <stdio.h>
#include <string.h>
#include "parser.h"

typedef struct parser_context_t {

  TERMINAL_T * current;
  TERMINAL_T * (*expect)();

} PARSER_CONTEXT_T;

typedef struct ast_specification_init {
  int rule_id;
  char * name;
  char * attr;
  int index;
} AST_SPECIFICATION_INIT;

static TERMINAL_T terminals[] = {
{% for terminal in nonAbstractTerminals %}
  { {{terminal.id}}, "{{terminal.string}}" },
{% endfor %}
};

static NONTERMINAL_T nonterminals[] = {
{% for nonterminal in grammar.nonterminals %}
  { {{nonterminal.id}}, "{{nonterminal.string}}" },
{% endfor %}
};

static int table[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)}}] = {
  {% py parseTable = grammar.getParseTable() %}
  {% for i in range(len(grammar.nonterminals)) %}
  { {{', '.join([str(rule.id) if rule else str(-1) for rule in parseTable[i]])}} },
  {% endfor %}
};

{% for exprGrammar in grammar.exprgrammars %}

static int infixBp_{{exprGrammar.nonterminal.string.lower()}}[{{len(grammar.terminals)}}] = {
  {% for i in range(len(grammar.terminals)) %}{{0 if i not in exprGrammar.infix else exprGrammar.infix[i]}}, {% endfor %}
};

static int prefixBp_{{exprGrammar.nonterminal.string.lower()}}[{{len(grammar.terminals)}}] = {
  {% for i in range(len(grammar.terminals)) %}{{0 if i not in exprGrammar.prefix else exprGrammar.prefix[i]}}, {% endfor %}
};

{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
{% py name = exprGrammar.nonterminal.string.lower() %}

static AST_SPECIFICATION_INIT ast_{{name}}[] = {
  {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
    {% if isinstance(rule.ast, AstSpecification) %}
      {% for i, key in enumerate(rule.ast.parameters.keys()) %}
  { {{rule.id}}, "{{rule.ast.name}}", "{{key}}", {{rule.ast.parameters[key]}} },
      {% endfor %}
    {% endif %}
  {% endfor %}
};

static int
getInfixBp_{{name}}(TERMINAL_E id)
{
  /* TODO: return index in infixBp_{{exprGrammar.nonterminal.string.lower()}} */
}

static int
getPrefixBp_{{name}}(TERMINAL_E id)
{
  /* TODO: return index in prefixBp_{{exprGrammar.nonterminal.string.lower()}} */
}

static PARSETREE_TO_AST_CONVERSION_T *
getAstConverter_{{name}}(int rule_id)
{
  static int dict = -1;
  PARSETREE_TO_AST_CONVERSION_T * converter;

  converter = calloc(1, sizeof(PARSETREE_TO_AST_CONVERSION_T));

  /* Create map (rule_id -> PARSETREE_TO_AST_CONVERSION_T) if it doesn't exist.  Then return result */

  if (0)
  {
    converter->type = AST_TRANSFORMATION;
    converter->object = NULL;
  }
  else if (0)
  {
    converter->type = AST_SPECIFICATION;
    converter->object = NULL;
  }
  else
  {

  }

  return NULL;
}

static PARSE_TREE_T *
nud_{{name}}(PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  int current = ctx->current->id; 
  int modifier = 0;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  if ( ctx->current == NULL )
    return tree;

  {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
    {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

    {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

    {% if len(ruleFirstSet) and not isOptional %}
  {{'if' if i == 0 else 'else if'}} ( {{' || '.join(['current == %d' % (x.id) for x in exprGrammar.ruleFirst(rule)])}} )
  {
      {% if len(rule.nudProduction) == 1 and isinstance(rule.nudProduction.morphemes[0], Terminal) %}
    tree->nchildren = 1;
    tree->children = calloc(1, sizeof(PARSE_TREE_NODE_T));
    tree->children[0].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[0].object = (PARSE_TREE_NODE_U *) ctx->expect( TERMINAL_{{rule.nudProduction.morphemes[0].string.upper()}} );
    return tree;
      {% else %}
    tree->ast_converter = getAstConverter_{{name}}({{rule.id}});
    tree->nchildren = {{len(rule.nudProduction)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nudProduction)}};
        {% for index, morpheme in enumerate(rule.nudProduction.morphemes) %}
          {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) ctx->expect( TERMINAL_{{morpheme.string.upper()}} );
          {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
            {% if isinstance(rule.operator, PrefixOperator) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = parse_{{rule.nonterminal.string.lower()}}( getPrefixBp_{{name}}({{rule.operator.operator.id}}) - modifier );
    tree->isPrefix = 1;
            {% else %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = parse_{{rule.nonterminal.string.lower()}}();
            {% endif %}
          {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = parse_{{morpheme.string.lower()}}();
          {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = parse_{{morpheme.start_nt.string.lower()}}();
          {% endif %}
        {% endfor %}
      {% endif %}
  }
  {% endif %}
  {% endfor %}

  return tree;
}

static PARSE_TREE_T *
led_{{name}}(PARSE_TREE_T * left, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  int modifier = 0;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  {% py seen = list() %}
  {% for rule in exprGrammar.rules %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) and led[0] not in seen %}
  {{'if' if len(seen)==0 else 'else if'}} ( ctx->current->id == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = getAstConverter_{{name}}({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nudProduction) == 1 and rule.nudProduction.morphemes[0] == rule.nonterminal%}
    tree->isExprNud = True
    {% endif %}

    /* TODO: this is wrong, actually need to copy left */
    tree->children[0] = left;

      {% for index, morpheme in enumerate(led) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) ctx->expect( TERMINAL_{{morpheme.string.upper()}} );
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
    modifier = {{1 if exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}};
          {% if isinstance(rule.operator, InfixOperator) %}
    tree->isInfix = 1;
          {% endif %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = parse_{{rule.nonterminal.string.lower()}}( getInfixBp_{{name}}({{rule.operator.operator.id}}) - modifier );
        {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = parse_{{morpheme.string.lower()}}();
        {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = parse_{{morpheme.start_nt.string.lower()}}();
        {% endif %}
      {% endfor %}
      {% py seen.append(led[0]) %}
  }
    {% endif %}
  {% endfor %}

  return tree;
}

static PARSE_TREE_T *
_parse_{{name}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{name}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( ctx->current && rbp < getInfixBp_{{name}}(ctx->current->id) )
  {
    left = led_{{name}}(left, ctx);
  }

  if ( left != NULL )
  {
    left->isExpr = 1;
  }

  return left;
}
{% endfor %}

{% if addMain %}
int main(int argc, char * argv[])
{
  printf("%s %s %d\n", terminals[1].string, nonterminals[0].string, table[1][2]);
}
{% endif %}
