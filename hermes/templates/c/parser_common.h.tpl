#ifndef __PARSER_COMMON_H
#define __PARSER_COMMON_H

typedef struct terminal_t {

  int id;
  char * string;

} TERMINAL_T;

typedef struct token_t {
  
  struct terminal_t * terminal;
  int lineno;
  int colno;
  char * source_string;
  char * resource;

} TOKEN_T;

typedef struct nonterminal_t {

  int id;
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

  int nonterminal;
  struct parse_tree_node_t * children;
  int nchildren;
  struct parsetree_to_ast_conversion_t * ast_converter;

  int isExpr;
  int isNud;
  int nudMorphemeCount;
  int isInfix;
  int isPrefix;
  int isExprNud;
  char * list;
  /* TODO: should be TERMINAL_E */
  union parse_tree_node_u * listSeparator;

} PARSE_TREE_T;

typedef union parse_tree_node_u {

  struct token_t terminal;
  struct parse_tree_t parse_tree;

} PARSE_TREE_NODE_U;

typedef enum ast_node_type_e {

  AST_NODE_TYPE_LIST,
  AST_NODE_TYPE_OBJECT,
  AST_NODE_TYPE_TERMINAL

} AST_NODE_TYPE_E;

typedef struct ast_list_t {

  struct abstract_syntax_tree_t * tree;
  struct ast_list_t * next;

} AST_LIST_T;

typedef struct ast_object_t {

  char * name;
  struct abstract_syntax_tree_attr_t * children;
  int nchildren;

} AST_OBJECT_T;

typedef struct abstract_syntax_tree_t {

  enum ast_node_type_e type;
  union ast_node_u * object;

} ABSTRACT_SYNTAX_TREE_T;

typedef struct abstract_syntax_tree_attr_t {

  char * name;
  struct abstract_syntax_tree_t * tree;

} ABSTRACT_SYNTAX_TREE_ATTR_T;

typedef union ast_node_u {

  struct terminal_t terminal;
  struct ast_object_t ast;
  struct ast_list_t list;

} AST_NODE_U;

typedef struct ast_object_attr_t {

  char * name;
  int index;

} AST_OBJECT_ATTR_T;

typedef struct ast_object_specification_t {

  char * name;
  struct ast_object_attr_t * attrs;
  int nattrs;

} AST_OBJECT_SPECIFICATION_T;

typedef struct ast_return_index_t {

  int index;

} AST_RETURN_INDEX_T;

typedef enum parsetree_to_ast_conversion_type_e {

  AST_RETURN_INDEX,
  AST_CREATE_OBJECT

} PARSETREE_TO_AST_CONVERSION_TYPE_E;

typedef struct parsetree_to_ast_conversion_t {

  enum parsetree_to_ast_conversion_type_e type;
  union parsetree_to_ast_conversion_u * object;

} PARSETREE_TO_AST_CONVERSION_T;

typedef union parsetree_to_ast_conversion_u {

  struct ast_object_specification_t specification;
  struct ast_return_index_t transformation;

} PARSE_TREE_TO_AST_CONVERSION_U;

typedef struct token_list_t {

  int current; /* terminal id */
  int current_index;
  TOKEN_T * tokens;
  int ntokens;

} TOKEN_LIST_T;

typedef struct syntax_error_t {

  TERMINAL_T * terminal;
  char * message;
  struct syntax_error_t * next;

} SYNTAX_ERROR_T;

typedef char * (*morpheme_to_str_func)(int);
typedef int (*str_to_morpheme_func)(const char *);

typedef struct parser_context_t {

  struct token_list_t * tokens;
  char * current_function;
  struct syntax_error_t * syntax_errors;
  struct syntax_error_t * last;
  morpheme_to_str_func morpheme_to_str;

} PARSER_CONTEXT_T;

typedef struct ast_object_specification_init {

  int rule_id;
  char * name;
  char * attr;
  int index;

} AST_CREATE_OBJECT_INIT;

char * ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree, PARSER_CONTEXT_T * ctx );
char * parsetree_to_string( PARSE_TREE_T * tree, PARSER_CONTEXT_T * ctx );
char * token_to_string(TOKEN_T * token, int indent, PARSER_CONTEXT_T * ctx);
ABSTRACT_SYNTAX_TREE_T * parsetree_node_to_ast( PARSE_TREE_NODE_T * node );
void free_parse_tree( PARSE_TREE_T * tree );
void free_ast( ABSTRACT_SYNTAX_TREE_T * ast );

#endif
