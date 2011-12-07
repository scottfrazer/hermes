#ifndef __{{}}_H
#define __{{}}_H

typedef struct terminal_t {

  int id;
  char * string_id;

} TERMINAL_T;

typedef union parse_tree_node_u {

  struct terminal_t terminal;
  struct parse_tree_t parse_tree;

} PARSE_TREE_NODE_U;

typedef enum parse_tree_node_type_e {

  PARSE_TREE_NODE_TYPE_TERMINAL;
  PARSE_TREE_NODE_TYPE_PARSETREE;

} PARSE_TREE_NODE_TYPE_E;

typedef struct parse_tree_node_t {

  enum parse_tree_node_type_e type;
  union parse_tree_node_u * object;

} PARSE_TREE_NODE_T;

typedef struct parse_tree_t {

  struct parse_tree_node_t * children;
  int nchildren;
  struct parsetree_to_ast_conversion_t * ast_converter;

} PARSE_TREE_T;

typedef struct abstract_syntax_tree_t {

  char * name;
  struct ast_specification_attributes_t * children;
  int nchildren;

} ABSTRACT_SYNTAX_TREE_T;

typedef struct ast_specification_attributes_t {

  char * name;
  int element;

} AST_SPECIFICATION_ATTRIBUTES_T;

typedef struct ast_transformation_t {

  int element;

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

  struct ast_specification_attributes_t;
  struct ast_transformation_t;

} PARSE_TREE_TO_AST_CONVERSION_U;

PARSE_TREE_T * parse( TOKEN_LIST_T * tokens );
ABSTRACT_SYNTAX_TREE_T * parse_tree_to_ast( PARSE_TREE_T * parse_tree );
void free_parse_tree( PARSE_TREE_T * tree );
void free_ast( ABSTRACT_SYNTAX_TREE_T * ast );
#endif
