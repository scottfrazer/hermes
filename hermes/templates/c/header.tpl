#ifndef __PARSER_H
#define __PARSER_H

typedef enum terminal_e {
{% for terminal in nonAbstractTerminals %}
  TERMINAL_{{terminal.string.upper()}} = {{terminal.id}},
{% endfor %}
} TERMINAL_E;

typedef enum nonterminal_e {
{% for nonterminal in grammar.nonterminals %}
  NONTERMINAL_{{nonterminal.string.upper()}} = {{nonterminal.id}},
{% endfor %}
} NONTERMINAL_E;

typedef struct terminal_t {

  enum terminal_e id;
  char * string;

} TERMINAL_T;

typedef struct nonterminal_t {

  enum terminal_e id;
  char * string;

} NONTERMINAL_T;

typedef enum parse_tree_node_type_e {

  PARSE_TREE_NODE_TYPE_TERMINAL,
  PARSE_TREE_NODE_TYPE_PARSETREE

} PARSE_TREE_NODE_TYPE_E;

typedef struct parse_tree_node_t {

  enum parse_tree_node_type_e type;
  union parse_tree_node_u * object;

} PARSE_TREE_NODE_T;

typedef struct parse_tree_t {

  enum nonterminal_e nonterminal;
  struct parse_tree_node_t * children;
  int nchildren;
  struct parsetree_to_ast_conversion_t * ast_converter;

  int isExpr;
  int isNud;
  int nudMorphemeCount;
  int isInfix;
  int isPrefix;

} PARSE_TREE_T;

typedef union parse_tree_node_u {

  struct terminal_t terminal;
  struct parse_tree_t parse_tree;

} PARSE_TREE_NODE_U;

typedef struct abstract_syntax_tree_attr_t {

  char * name;
  struct abstract_syntax_tree_t * attr;

} ABSTRACT_SYNTAX_TREE_ATTR_T;

typedef struct abstract_syntax_tree_t {

  char * name;
  struct abstract_syntax_tree_attr_t * children;
  int nchildren;

} ABSTRACT_SYNTAX_TREE_T;

typedef struct ast_specification_attr_t {

  char * name;
  int index;

} AST_SPECIFICATION_ATTR_T;

typedef struct ast_specification_t {

  char * name;
  struct ast_specification_attr_t * attrs;
  int nattrs;

} AST_SPECIFICATION_T;

typedef struct ast_transformation_t {

  int index;

} AST_TRANSFORMATION_T;

typedef enum parsetree_to_ast_conversion_type_e {

  AST_TRANSFORMATION,
  AST_SPECIFICATION

} PARSETREE_TO_AST_CONVERSION_TYPE_E;

typedef struct parsetree_to_ast_conversion_t {

  enum parsetree_to_ast_conversion_type_e type;
  union parsetree_to_ast_conversion_u * object;

} PARSETREE_TO_AST_CONVERSION_T;

typedef union parsetree_to_ast_conversion_u {

  struct ast_specification_t specification;
  struct ast_transformation_t transformation;

} PARSE_TREE_TO_AST_CONVERSION_U;

typedef struct token_list_t {

  int x;

} TOKEN_LIST_T;

PARSE_TREE_T * parse( TOKEN_LIST_T * tokens ) {}
ABSTRACT_SYNTAX_TREE_T * parse_tree_to_ast( PARSE_TREE_T * parse_tree );
void free_parse_tree( PARSE_TREE_T * tree );
void free_ast( ABSTRACT_SYNTAX_TREE_T * ast );
#endif
