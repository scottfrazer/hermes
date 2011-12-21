{% from hermes.Grammar import AstTranslation, AstSpecification, ExprRule %}
{% from hermes.Grammar import PrefixOperator, InfixOperator, MixfixOperator %}
{% from hermes.Macro import SeparatedListMacro, NonterminalListMacro, TerminatedListMacro, LL1ListMacro, MinimumListMacro, OptionalMacro %}
{% from hermes.Morpheme import Terminal, NonTerminal %}
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "parser.h"

{% for nonterminal in LL1Nonterminals %}
static PARSE_TREE_T * parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
static PARSE_TREE_T * parse_{{exprGrammar.nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
static PARSE_TREE_T * _parse_{{exprGrammar.nonterminal.string.lower()}}(int, PARSER_CONTEXT_T *);
{% endfor %}

static ABSTRACT_SYNTAX_TREE_T *
_parsetree_node_to_ast( PARSE_TREE_NODE_T * node );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_normal( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_expr( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast );

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast );

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent );

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent );

static char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent );

typedef struct ast_object_specification_init {
  int rule_id;
  char * name;
  char * attr;
  int index;
} AST_CREATE_OBJECT_INIT;

static int
in_array(int * array, int element )
{
  /* -2 terminated arrays */
  int i;
  for ( i=0; array[i] != -2; i++ )
  {
    if ( array[i] == element )
      return 1;
  }
  return 0;
}

static PARSE_TREE_NODE_U *
copy_parse_tree(PARSE_TREE_T * tree)
{
  PARSE_TREE_T * new;
  new = calloc(1, sizeof(PARSE_TREE_T));
  memcpy(new, tree, sizeof(PARSE_TREE_T));
  new->children = calloc(new->nchildren, sizeof(PARSE_TREE_NODE_T));
  memcpy(new->children, tree->children, new->nchildren * sizeof(PARSE_TREE_NODE_T));
  return (PARSE_TREE_NODE_U *) new;
}

static int
is_terminal(int id)
{
  return (0 <= id && id <= {{len(nonAbstractTerminals) - 1}});
}

static int
is_nonterminal(int id)
{
  return ({{len(nonAbstractTerminals)}} <= id && id <= {{len(nonAbstractTerminals) + len(grammar.nonterminals) - 1}});
}

static TERMINAL_E
advance(PARSER_CONTEXT_T * ctx)
{
  TOKEN_LIST_T * token_list = ctx->tokens;
  if ( token_list->current_index == token_list->ntokens )
  {
    return TERMINAL_NONE;
  }
  token_list->current_index += 1;
  token_list->current = token_list->tokens[token_list->current_index].id;
  return token_list->current;
}

static TERMINAL_T *
expect(TERMINAL_E terminal_id, PARSER_CONTEXT_T * ctx)
{
  TERMINAL_E current, next;
  TERMINAL_T * current_token;
  TOKEN_LIST_T * token_list = ctx->tokens;

  if ( token_list == NULL )
  {
    perror("expect");
    /* "No more tokens.  Expecting %s' % (self.terminals[terminalId])" */
  }

  current = token_list->tokens[token_list->current_index].id;
  if ( current != terminal_id )
  {
    perror("expect");
    /* raise SyntaxError( 'Unexpected symbol when parsing %s.  Expected %s, got %s.' %(whosdaddy(), self.terminals[terminalId], current if current else 'None') ) */
  }

  current_token = &token_list->tokens[token_list->current_index];
  next = advance(ctx);

  if ( next != TERMINAL_NONE && !is_terminal(next) )
  {
    perror("expect");
    /* raise SyntaxError( 'Invalid symbol ID: %d (%s)' % (nextToken.getId(), nextToken) ) */
  }

  return current_token;
}

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E ast_types[{{len(grammar.rules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

static AST_CREATE_OBJECT_INIT ast_objects[] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
      {% for i, key in enumerate(rule.ast.parameters.keys()) %}
  { {{rule.id}}, "{{rule.ast.name}}", "{{key}}", {{rule.ast.parameters[key]}} },
      {% endfor %}
    {% endif %}
  {% endfor %}
  {0}
};

static int ast_index[{{len(grammar.expandedRules)}}] = {
  {% for rule in sorted(grammar.expandedRules, key=lambda x: x.id) %}
  {{rule.ast.idx if isinstance(rule.ast, AstTranslation) else 0}},
  {% endfor %}
};

static PARSETREE_TO_AST_CONVERSION_T *
get_ast_converter(int rule_id)
{
  PARSETREE_TO_AST_CONVERSION_T * converter = NULL;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;
  AST_RETURN_INDEX_T * ast_return_index;
  PARSETREE_TO_AST_CONVERSION_TYPE_E conversion_type;
  int i, j, nattrs;

  converter = calloc(1, sizeof(PARSETREE_TO_AST_CONVERSION_T));
  conversion_type = ast_types[rule_id];

  /* Create map (rule_id -> PARSETREE_TO_AST_CONVERSION_T) if it doesn't exist.  Then return result */

  if (conversion_type == AST_RETURN_INDEX)
  {
    ast_return_index = calloc(1, sizeof(AST_RETURN_INDEX_T));
    ast_return_index->index = ast_index[rule_id];
    converter->type = AST_RETURN_INDEX;
    converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_return_index;
  }
  
  if (conversion_type == AST_CREATE_OBJECT)
  {
    ast_object_spec = calloc(1, sizeof(AST_OBJECT_SPECIFICATION_T));
    for ( i = 0, nattrs = 0; ast_objects[i].name != NULL; i++ )
    {
      if ( ast_objects[i].rule_id == rule_id )
        nattrs += 1;
    }

    ast_object_spec->attrs = calloc(nattrs, sizeof(AST_OBJECT_ATTR_T));
    ast_object_spec->nattrs = nattrs;

    for ( i = 0, j = 0; ast_objects[i].name != NULL; i++ )
    {
      if ( ast_objects[i].rule_id == rule_id )
      {
        ast_object_spec->name = ast_objects[i].name;
        ast_object_spec->attrs[j].name = ast_objects[i].attr;
        ast_object_spec->attrs[j].index = ast_objects[i].index;
        j += 1;
      }
    }
    converter->type = AST_CREATE_OBJECT;
    converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_object_spec;
  }

  return converter;
}

/* index with TERMINAL_E or NONTERMINAL_E */
static char * morphemes[] = {
{% for terminal in sorted(nonAbstractTerminals, key=lambda x: x.id) %}
  "{{terminal.string}}", /* {{terminal.id}} */
{% endfor %}

{% for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.id) %}
  "{{nonterminal.string}}", /* {{nonterminal.id}} */
{% endfor %}
};

static char *
nonterminal_to_str(NONTERMINAL_E nonterminal)
{
  return morphemes[nonterminal];
}

static char *
terminal_to_str(TERMINAL_E terminal)
{
  return morphemes[terminal];
}

static int first[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.first[nonterminal]])}}{{', ' if len(grammar.first[nonterminal]) else ''}}-2 },
{% endfor %}
};

static int follow[{{len(grammar.nonterminals)}}][{{len(nonAbstractTerminals)}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.follow[nonterminal]])}}{{', ' if len(grammar.follow[nonterminal]) else ''}}-2 },
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

static int
getInfixBp_{{name}}(TERMINAL_E id)
{
  /* TODO: return index in infixBp_{{exprGrammar.nonterminal.string.lower()}} */
  return infixBp_{{name}}[id];
}

static int
getPrefixBp_{{name}}(TERMINAL_E id)
{
  /* TODO: return index in prefixBp_{{exprGrammar.nonterminal.string.lower()}} */
  return prefixBp_{{name}}[id];
}

static PARSE_TREE_T *
nud_{{name}}(PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  TERMINAL_E current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% for i, rule in enumerate(exprGrammar.getExpandedRules()) %}
    {% py ruleFirstSet = exprGrammar.ruleFirst(rule) if isinstance(rule, ExprRule) else set() %}

    {% py isOptional = isinstance(rule, ExprRule) and len(rule.nudProduction.morphemes) and isinstance(rule.nudProduction.morphemes[0], NonTerminal) and rule.nudProduction.morphemes[0].macro and isinstance(rule.nudProduction.morphemes[0].macro, OptionalMacro) and rule.nudProduction.morphemes[0].macro.nonterminal == exprGrammar.nonterminal %}

    {% if len(ruleFirstSet) and not isOptional %}
  {{'if' if i == 0 else 'else if'}} ( {{' || '.join(['current == %d' % (x.id) for x in exprGrammar.ruleFirst(rule)])}} )
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(rule.nudProduction)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nudProduction)}};
    {% for index, morpheme in enumerate(rule.nudProduction.morphemes) %}
      {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( TERMINAL_{{morpheme.string.upper()}}, ctx );
    {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}

        {% if isinstance(rule.operator, PrefixOperator) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) _parse_{{rule.nonterminal.string.lower()}}( getPrefixBp_{{name}}({{rule.operator.operator.id}}) - modifier, ctx );
    tree->isPrefix = 1;
        {% else %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{rule.nonterminal.string.lower()}}(ctx);
        {% endif %}

    {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
      {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.start_nt.string.lower()}}(ctx);
      {% endif %}
    {% endfor %}
  }
  {% endif %}
  {% endfor %}

  return tree;
}

static PARSE_TREE_T *
led_{{name}}(PARSE_TREE_T * left, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  TERMINAL_E current = ctx->tokens->current; 
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% py seen = list() %}
  {% for rule in exprGrammar.getExpandedRules() %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) and led[0] not in seen %}
  {{'if' if len(seen)==0 else 'else if'}} ( current == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nudProduction) == 1 and rule.nudProduction.morphemes[0] == rule.nonterminal%}
    tree->isExprNud = 1; 
    {% endif %}

    /* TODO: this is wrong, actually need to copy left */
    tree->children[0].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[0].object = left;

      {% for index, morpheme in enumerate(led) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) expect( TERMINAL_{{morpheme.string.upper()}}, ctx );
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
    modifier = {{1 if rule.operator.operator.id in exprGrammar.precedence and exprGrammar.precedence[rule.operator.operator.id] == 'right' else 0}};
          {% if isinstance(rule.operator, InfixOperator) %}
    tree->isInfix = 1;
          {% endif %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) _parse_{{rule.nonterminal.string.lower()}}( getInfixBp_{{name}}({{rule.operator.operator.id}}) - modifier, ctx );
        {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
        {% elif isinstance(morpheme, LL1ListMacro) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.start_nt.string.lower()}}(ctx);
        {% endif %}
      {% endfor %}
      {% py seen.append(led[0]) %}
  }
    {% endif %}
  {% endfor %}

  return tree;
}
{% endfor %}

{% for nonterminal in LL1Nonterminals %}

static PARSE_TREE_T *
parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  TERMINAL_E current;
  TOKEN_LIST_T * tokens = ctx->tokens;
  PARSE_TREE_T * tree, * subtree;
  int rule;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = NONTERMINAL_{{nonterminal.string.upper()}};

  rule = -1;
  if ( tokens != NULL )
  {
    current = tokens->current;
    rule = table[{{nonterminal.id - len(nonAbstractTerminals)}}][current];
  }

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
  tree->list = "slist";
    {% elif isinstance(nonterminal.macro, NonterminalListMacro) %}
  tree->list = "nlist";
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
  tree->list = "tlist";
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
  tree->list = "mlist";
    {% else %}
  tree->list = NULL;
    {% endif %}

    {% if nonterminal.empty %}
  if ( tokens != NULL && in_array(follow[NONTERMINAL_{{nonterminal.string.upper()}} - {{len(nonAbstractTerminals)}}], current))
  {
    return tree;
  }
    {% endif %}

  if ( tokens == NULL )
  {
    {% if nonterminal.empty or grammar.ε in grammar.first[nonterminal] %}
    return tree;
    {% else %}
    /* TODO: raise SyntaxError('Error: unexpected end of file') */
    {% endif %}
  }


    {% for index0, rule in enumerate(nonterminal.rules) %}
      {% if index0 == 0 %}
  if ( rule == {{rule.id}} )
      {% else %}
  else if ( rule == {{rule.id}} )
      {% endif %}
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->children = calloc({{len(rule.production.morphemes)}}, sizeof(PARSE_TREE_NODE_T));
    tree->nchildren = {{len(rule.production.morphemes)}};
      {% for index, morpheme in enumerate(rule.production.morphemes) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% if isinstance(nonterminal.macro, SeparatedListMacro) and index == 0 %}
    tree->listSeparator = tree->children[{{index}}].object;
          {% endif %}
        {% endif %}

        {% if isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
        {% endif %}
      {% endfor %}

    return tree;
  }
    {% endfor %}

    {% for exprGrammar in grammar.exprgrammars %}
      {% if grammar.getExpressionTerminal(exprGrammar) in grammar.first[nonterminal] %}
        {% set grammar.getRuleFromFirstSet(nonterminal, {grammar.getExpressionTerminal(exprGrammar)}) as rule %}

  else if ( in_array(first[NONTERMINAL_{{exprGrammar.nonterminal.string.upper()}} - {{len(nonAbstractTerminals)}}], current) )
  {
    tree->ast_converter = get_ast_converter({{rule.id}});

        {% for index, morpheme in enumerate(rule.production.morphemes) %}

          {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% endif %}

          {% if isinstance(morpheme, NonTerminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
          {% endif %}
        {% endfor %}
  }
      {% endif %}
    {% endfor %}

    {% if not nonterminal.empty %}
  /* TODO: raise SyntaxError('Error: Unexpected symbol (%s) when parsing %s' % (current, whoami())) */
  return NULL;
    {% else %}
  return tree;
    {% endif %}
}
{% endfor %}

{% for exprGrammar in grammar.exprgrammars %}
static PARSE_TREE_T *
_parse_{{exprGrammar.nonterminal.string.lower()}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{name}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( ctx->tokens->current && rbp < getInfixBp_{{exprGrammar.nonterminal.string.lower()}}(ctx->tokens->current) )
  {
    left = led_{{name}}(left, ctx);
  }

  if ( left != NULL )
  {
    left->isExpr = 1;
  }

  return left;
}

static PARSE_TREE_T *
parse_{{exprGrammar.nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  return _parse_{{exprGrammar.nonterminal.string.lower()}}(0, ctx);
}
{% endfor %}

typedef PARSE_TREE_T * (*parse_function)(PARSER_CONTEXT_T *);

static parse_function
functions[{{len(grammar.nonterminals)}}] = {

  {% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  parse_{{nonterminal.string.lower()}},
  {% endfor %}

};

PARSER_CONTEXT_T *
parser_init( TOKEN_LIST_T * tokens )
{
  PARSER_CONTEXT_T * ctx;
  ctx = calloc(1, sizeof(PARSER_CONTEXT_T));
  ctx->tokens = tokens;
  tokens->current_index = 0;
  tokens->current = tokens->tokens[0].id;
  return ctx;
}

void
parser_exit( PARSER_CONTEXT_T * ctx)
{
  free(ctx);
}

PARSE_TREE_T *
parse(TOKEN_LIST_T * tokens, NONTERMINAL_E start, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;

  if ( start == -1 )
    start = NONTERMINAL_{{grammar.start.string.upper()}};

  tree = functions[start - {{len(nonAbstractTerminals)}}](ctx);

  /* TODO: init the parser_context_t here? */

  if ( tokens->current != TERMINAL_NONE )
  {
    /* TODO: SyntaxError( 'Finished parsing without consuming all tokens.' ) */
  }

  return tree;
}

ABSTRACT_SYNTAX_TREE_T *
parsetree_to_ast( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return _parsetree_node_to_ast(&node);
}

static ABSTRACT_SYNTAX_TREE_T *
_parsetree_node_to_ast( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast;
  PARSE_TREE_T * tree;
  PARSE_TREE_NODE_T * child;
  int i, index;
  char * name;

  ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    ast->type = AST_NODE_TYPE_TERMINAL;
    ast->object = (AST_NODE_U *) node->object;
    return ast;
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->list && strlen(tree->list) )
    {
      return __parsetree_node_to_ast_list(node, ast);
    }
    else if ( tree->isExpr )
    {
      return __parsetree_node_to_ast_expr(node, ast);
    }
    else
    {
      return __parsetree_node_to_ast_normal(node, ast);
    }
  }

  return NULL;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast )
{
  AST_LIST_T * item, * lnode, * tail, * ast_list;
  ABSTRACT_SYNTAX_TREE_T * this, * next;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  int offset, i;
  ast->type = AST_NODE_TYPE_LIST;
  ast->object = NULL;

  if ( tree->nchildren == 0 )
    return NULL;

  if ( !strcmp(tree->list, "slist") || !strcmp(tree->list, "nlist") )
  {
    offset = (tree->children[0].object == tree->listSeparator) ? 1 : 0;
    this = _parsetree_node_to_ast(&tree->children[offset]);
    next = _parsetree_node_to_ast(&tree->children[offset + 1]);

    ast_list = NULL;
    if ( this != NULL )
    {
      ast_list = calloc(1, sizeof(AST_LIST_T));
      ast_list->tree = this;
      ast_list->next = NULL;

      if ( next != NULL )
      {
        ast_list->next = (AST_LIST_T *) next->object;
      }
    }
  }
  else if ( !strcmp(tree->list, "tlist") )
  {
    this = _parsetree_node_to_ast(&tree->children[0]);
    next = _parsetree_node_to_ast(&tree->children[2]);

    ast_list = NULL;
    if ( this != NULL )
    {
      ast_list = calloc(1, sizeof(AST_LIST_T));
      ast_list->tree = this;
      ast_list->next = NULL;

      if ( next != NULL )
      {
        ast_list->next = (AST_LIST_T *) next->object;
      }
    }
  }
  else if ( !strcmp(tree->list, "mlist") )
  {
    lnode = ast_list = tail = NULL;
    for ( i = 0; i < tree->nchildren - 1; i++ )
    {
      lnode = calloc(1, sizeof(AST_LIST_T));
      lnode->tree = _parsetree_node_to_ast(&tree->children[i]);

      if ( ast_list == NULL )
      {
        ast_list = tail = lnode;
        continue;
      }

      tail->next = (AST_LIST_T *) lnode;
      tail = tail->next;
    }
  }

  ast->object = (AST_NODE_U *) ast_list;
  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_expr( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast )
{
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object, * first;
  AST_OBJECT_T * ast_object;
  PARSETREE_TO_AST_CONVERSION_T * ast_converter = tree->ast_converter;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) ast_converter->object;
  AST_RETURN_INDEX_T * ast_return_index = (AST_RETURN_INDEX_T *) ast_converter->object;
  PARSE_TREE_NODE_T * child;
  int index, i;

  if ( tree->ast_converter->type == AST_RETURN_INDEX )
  {
    free(ast);
    return _parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( tree->ast_converter->type == AST_CREATE_OBJECT )
  {
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name) + 1, sizeof(char));
    strcpy(ast_object->name, ast_object_spec->name);

    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));
    ast_object->nchildren = ast_object_spec->nattrs;

    ast->object = (AST_NODE_U *) ast_object;
    ast->type = AST_NODE_TYPE_OBJECT;

    for ( i = 0; i < ast_object_spec->nattrs; i++ )
    {
      ast_object->children[i].name = ast_object_spec->attrs[i].name;
      index = ast_object_spec->attrs[i].index;

      /* TODO: omg seriously? */
      if ( index == '$' )
      {
        child = &tree->children[0];
      }
      else if ( tree->children[0].type == PARSE_TREE_NODE_TYPE_PARSETREE &&
                ((PARSE_TREE_T *) tree->children[0].object)->isNud &&
                !((PARSE_TREE_T *) tree->children[0].object)->isPrefix &&
                !tree->isExprNud &&
                !tree->isInfix )
      {
        first = (PARSE_TREE_T *) tree->children[0].object;
        if ( index < first->nudMorphemeCount )
        {
          child = &first->children[index];
        }
        else
        {
          child = &tree->children[index - first->nudMorphemeCount + 1];
        }
      }
      else if ( tree->nchildren == 1 && tree->children[0].type != PARSE_TREE_NODE_TYPE_PARSETREE )
      {
        return _parsetree_node_to_ast( &tree->children[0] );
      }
      else
      {
        child = &tree->children[index];
      }

      ast_object->children[i].tree = _parsetree_node_to_ast(child);
    }

    return ast;
  }

  return NULL;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_normal( PARSE_TREE_NODE_T * node, ABSTRACT_SYNTAX_TREE_T * ast )
{
  AST_OBJECT_T * ast_object;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  PARSETREE_TO_AST_CONVERSION_T * ast_converter = tree->ast_converter;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) ast_converter->object;
  AST_RETURN_INDEX_T * ast_return_index = (AST_RETURN_INDEX_T *) ast_converter->object;
  int i;

  if ( tree->ast_converter->type == AST_RETURN_INDEX )
  {
    free(ast);
    return _parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( tree->ast_converter->type == AST_CREATE_OBJECT )
  {
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name)+1, sizeof(char));
    strcpy( ast_object->name, ast_object_spec->name );
    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));
    ast_object->nchildren = ast_object_spec->nattrs;

    for ( i = 0; i < ast_object_spec->nattrs; i++ )
    {
      ast_object->children[i].name = ast_object_spec->attrs[i].name;
      ast_object->children[i].tree = _parsetree_node_to_ast(&tree->children[ast_object_spec->attrs[i].index]);
    }

    ast->object = (AST_NODE_U *) ast_object;
    ast->type = AST_NODE_TYPE_OBJECT;
    return ast;
  }
  return NULL;
}

static char *
_get_indent_str(int length)
{
  char * str = malloc(length + 1 * sizeof(char));
  memset(str, ' ', length);
  str[length] = '\0';
  return str;
}

char *
parsetree_to_string( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  char * str;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return _parsetree_to_string(&node, 0);
}

static int
_parsetree_to_string_bytes( PARSE_TREE_NODE_T * node, int indent )
{
  PARSE_TREE_T * tree;
  TERMINAL_T * terminal;
  int bytes, i;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      /* format: "(nonterminal: )" */
      return 4 + strlen(nonterminal_to_str(tree->nonterminal));
    }
    else
    {
      bytes = (5 + indent + strlen(nonterminal_to_str(tree->nonterminal)));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        bytes += 2 + indent + _parsetree_to_string_bytes(&tree->children[i], indent + 2);
      }
      bytes += (tree->nchildren - 1) * 2;
      return bytes;
    }
  }
  
  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    return strlen(terminal_to_str(terminal->id));
  }

  return -1;
}

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent )
{
  PARSE_TREE_T * tree;
  TERMINAL_T * terminal;
  char * str, * tmp, * indent_str;
  int bytes, i, len;

  bytes = _parsetree_to_string_bytes(node, indent);
  bytes += 1; /* null bytes */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      snprintf(str, bytes, "(%s: )", nonterminal_to_str(tree->nonterminal));
    }
    else
    {
      indent_str = _get_indent_str(indent);
      snprintf(str, bytes, "(%s:\n", nonterminal_to_str(tree->nonterminal));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        if ( i != 0 )
        {
          strcat(str, ",\n");
        }

        len = strlen(str);
        tmp = _parsetree_to_string(&tree->children[i], indent + 2);
        snprintf(str + len, bytes - len, "%s  %s", indent_str, tmp);
        free(tmp);
      }
      len = strlen(str);
      snprintf(str + len, bytes - len, "\n%s)", indent_str);
      free(indent_str);
    }
    return str;
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    strcpy(str, terminal_to_str(terminal->id));
    return str;
  }

  return NULL;
}

static char *
_lstrip(char * string)
{
  char * tmp, * stripped;
  for ( tmp = string; *tmp == ' '; tmp++ );
  stripped = calloc(strlen(tmp) + 1, sizeof(char));
  strcpy(stripped, tmp);
  return stripped;
}

char *
ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree )
{
  return _ast_to_string(tree, 0);
}

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * list_node;
  TERMINAL_T * terminal;
  int i, bytes;

  if ( node->type == AST_NODE_TYPE_OBJECT )
  {
    ast_object = (AST_OBJECT_T *) node->object;
    bytes = 3 + indent + strlen(ast_object->name);

    for ( i = 0; i < ast_object->nchildren; i++ )
    {
      if ( i != 0 )
        bytes += 2;
      bytes += 3 + strlen(ast_object->children[i].name) + _ast_to_string_bytes(ast_object->children[i].tree, indent + 2);
    }

    bytes += 2 + indent;
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list->tree == NULL )
    {
      return 2; /* "[]" */
    }

    bytes = 4 + indent;
    for ( i = 0, list_node = ast_list; list_node && list_node->tree; i++, list_node = list_node->next )
    {
      if ( i != 0 )
        bytes += 2;
      bytes += _ast_to_string_bytes(list_node->tree, indent + 2);
    }
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    return indent + strlen(terminal_to_str(terminal->id));
  }

  return 4; /* "None" */
}

char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent )
{
  AST_LIST_T * ast_list, * lnode;
  AST_OBJECT_T * ast_object;
  TERMINAL_T * terminal;
  char * str, * key, * value, * indent_str, * tmp;
  int bytes, i;

  bytes = _ast_to_string_bytes(node, indent) + 1;
  str = calloc( bytes, sizeof(char) );

  if ( node->type == AST_NODE_TYPE_OBJECT )
  {
    indent_str = _get_indent_str(indent);
    ast_object = (AST_OBJECT_T *) node->object;
    snprintf(str, bytes,"%s(%s:\n", indent_str, ast_object->name);

    for ( i = 0; i < ast_object->nchildren; i++ )
    {
      if ( i != 0 )
        strcat(str, ",\n");

      key = ast_object->children[i].name;
      value = _ast_to_string(ast_object->children[i].tree, indent + 2);

      if ( *value == ' ' )
      {
        tmp = value;
        value = _lstrip(value);
        free(tmp);
      }

      snprintf(str + strlen(str), bytes - strlen(str), "%s  %s=%s", indent_str, key, value);
      free(value);
    }

    snprintf(str + strlen(str), bytes - strlen(str), "\n%s)", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list == NULL )
    {
      strcpy(str, "[]");
      return str;
    }
    
    snprintf(str, bytes, "[\n");
    for ( i = 0, lnode = ast_list; lnode && lnode->tree; i++, lnode = lnode->next )
    {
      value = _ast_to_string(lnode->tree, indent + 2);
      snprintf(str + strlen(str), bytes - strlen(str), "%s", value);
      if ( lnode->next != NULL )
        strcat(str, ",\n");
      free(value);
    }
    indent_str = _get_indent_str(indent);
    snprintf(str + strlen(str), bytes - strlen(str), "\n%s]", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    terminal = (TERMINAL_T *) node->object;
    strcpy(str, terminal_to_str(terminal->id));
    return str;
  }

  strcpy(str, "None");
  return str;
}

void
free_parse_tree( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  _free_parse_tree(&node);
}

void
_free_parse_tree( PARSE_TREE_NODE_T * node )
{
  int i;
  TERMINAL_T * terminal;
  PARSE_TREE_T * tree;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->ast_converter )
    {
      if ( tree->ast_converter->object )
      {
        if ( tree->ast_converter->type == AST_CREATE_OBJECT )
        {
          ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) tree->ast_converter->object;
          free(ast_object_spec->attrs);
        }
        free(tree->ast_converter->object);
      }

      free(tree->ast_converter);
    }

    for ( i = 0; i < tree->nchildren; i++ )
    {
      _free_parse_tree(&tree->children[i]);
    }

    free(tree->children);
    free(tree);
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    /* Terminals are provided by the user and don't need to be freed */
    terminal = (TERMINAL_T *) node->object;
  }
}

void
free_ast( ABSTRACT_SYNTAX_TREE_T * ast )
{

}

{% if addMain %}
int
main(int argc, char * argv[])
{
  PARSE_TREE_T * tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * ast;
  TOKEN_LIST_T token_list;
  char * str;

  TERMINAL_T tokens[{{len(initialTerminals)}}] = {
    {% for terminal in initialTerminals %}
    {TERMINAL_{{terminal.upper()}}, "" },
    {% endfor %}
  };

  token_list.tokens = tokens;
  token_list.ntokens = {{len(initialTerminals)}};
  token_list.current = tokens[0].id;
  token_list.current_index = 0;

  ctx = parser_init(&token_list);

  tree = parse(&token_list, -1, ctx);
  if ( tree == NULL || argc <= 1 || (argc > 1 && !strcmp(argv[1], "parsetree")) )
  {
    str = parsetree_to_string(tree);
  }
  else if ( argc > 1 && !strcmp(argv[1], "ast") )
  {
    ast = parsetree_to_ast(tree);
    str = ast_to_string(ast);
    free(ast);
  }
  printf("%s\n", str);

  free_parse_tree(tree);
  parser_exit(ctx);
  free(str);
  return 0;
}
{% endif %}
