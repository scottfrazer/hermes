#ifndef HERMES_PARSER_COMMON_H
#define HERMES_PARSER_COMMON_H

#include <pcre.h>

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
  int list; /* boolean */
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
  TOKEN_T ** tokens;
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

typedef struct lexer_context_t {
    char * string;
    char * resource;
    void * user_context;
    int * stack;    /* Stack of mode enums */
    int stack_size; /* Allocated size of 'stack' */
    int stack_top;  /* index into 'stack' */
    TOKEN_LIST_T * token_list;
    int line;
    int col;
} LEXER_CONTEXT_T;

typedef void (*lexer_match_function)(
    LEXER_CONTEXT_T * ctx,
    TERMINAL_T * terminal,
    char * source_string,
    int line,
    int col
);

typedef struct lexer_regex_output_t {
    TERMINAL_T * terminal;
    int group;
    lexer_match_function match_func;
    char * stack_push;
    char * action;
} LEXER_REGEX_OUTPUT_T;

typedef struct lexer_regex_t {
    pcre * regex;
    const char * pcre_errptr;
    int pcre_erroffset;
    char * pattern;
    LEXER_REGEX_OUTPUT_T * outputs;
    int outputs_count;
} LEXER_REGEX_T;

typedef struct lexer_regex_t *** LEXER_T;

#endif

char * {{prefix}}ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree, PARSER_CONTEXT_T * ctx );
char * {{prefix}}parsetree_to_string( PARSE_TREE_T * tree, PARSER_CONTEXT_T * ctx );
char * {{prefix}}token_to_string(TOKEN_T * token);
ABSTRACT_SYNTAX_TREE_T * {{prefix}}parsetree_node_to_ast( PARSE_TREE_NODE_T * node );
void {{prefix}}free_parse_tree( PARSE_TREE_T * tree );
void {{prefix}}free_ast( ABSTRACT_SYNTAX_TREE_T * ast );

#ifndef __HERMES_{{prefix.upper()}}PARSER_H

/* Section: Parser */

#define {{prefix.upper()}}TERMINAL_COUNT {{len(grammar.standard_terminals)}}
#define {{prefix.upper()}}NONTERMINAL_COUNT {{len(grammar.nonterminals)}}

typedef enum {{prefix}}terminal_e {

{% for terminal in grammar.standard_terminals %}
  {{prefix.upper()}}TERMINAL_{{terminal.string.upper()}} = {{terminal.id}},
{% endfor %}
  {{prefix.upper()}}TERMINAL_END_OF_STREAM = -1

} ENUM_{{prefix.upper()}}TERMINAL;

typedef enum {{prefix}}nonterminal_e {

{% for nonterminal in grammar.nonterminals %}
  {{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} = {{nonterminal.id}},
{% endfor %}
  {{prefix.upper()}}NONTERMINAL_END_OF_STREAM = -1

} ENUM_{{prefix.upper()}}NONTERMINAL;

#define {{prefix.upper()}}IS_TERMINAL(id) \
  (0 <= id && id <= {{len(grammar.standard_terminals) - 1}})

#define {{prefix.upper()}}IS_NONTERMINAL(id) \
  ({{len(grammar.standard_terminals)}} <= id && id <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}})

PARSER_CONTEXT_T * {{prefix}}parser_init( TOKEN_LIST_T * tokens );
void {{prefix}}parser_exit( PARSER_CONTEXT_T * ctx);
PARSE_TREE_T * {{prefix}}parse(PARSER_CONTEXT_T * ctx, ENUM_{{prefix.upper()}}NONTERMINAL start);
ABSTRACT_SYNTAX_TREE_T *{{prefix}}ast( PARSE_TREE_T * parse_tree );
void * {{prefix}}eval( PARSE_TREE_T * parse_tree );
char * {{prefix}}morpheme_to_str(int id);
int {{prefix}}str_to_morpheme(const char * str);

/* Section: Lexer */

{% if lexer %}

typedef enum {{prefix}}lexer_mode_e {
{% for mode, regex_list in lexer.items() %}
  {{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E,
{% endfor %}
  {{prefix.upper()}}LEXER_INVALID_MODE_E,
} {{prefix.upper()}}LEXER_MODE_E;

void {{prefix}}lexer_init();
int {{prefix}}lexer_has_errors();
void {{prefix}}lexer_print_errors();
void {{prefix}}lexer_destroy();
{{prefix.upper()}}LEXER_MODE_E {{prefix}}lexer_mode(const char * mode);
char * {{prefix}}lexer_mode_string({{prefix.upper()}}LEXER_MODE_E mode);
TOKEN_LIST_T * {{prefix}}lex(char * string, char * resource, char * error);
void {{prefix}}free_token_list(TOKEN_LIST_T * list);

{% endif %}

#endif
