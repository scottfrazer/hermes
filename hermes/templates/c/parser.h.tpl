#ifndef __{{prefix.upper()}}_PARSER_H
#define __{{prefix.upper()}}_PARSER_H

#include "parser_common.h"

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

#define {{prefix.upper()}}IS_TERMINAL(id) (0 <= id && id <= {{len(grammar.standard_terminals) - 1}})
#define {{prefix.upper()}}IS_NONTERMINAL(id) ({{len(grammar.standard_terminals)}} <= id && id <= {{len(grammar.standard_terminals) + len(grammar.nonterminals) - 1}})

PARSER_CONTEXT_T *
{{prefix}}parser_init( TOKEN_LIST_T * tokens );

void
{{prefix}}parser_exit( PARSER_CONTEXT_T * ctx);

PARSE_TREE_T *
{{prefix}}parse( TOKEN_LIST_T * tokens, int start, PARSER_CONTEXT_T * ctx );

ABSTRACT_SYNTAX_TREE_T *
{{prefix}}ast( PARSE_TREE_T * parse_tree );

void *
{{prefix}}eval( PARSE_TREE_T * parse_tree );

char *
{{prefix}}morpheme_to_str(int id);

int
{{prefix}}str_to_morpheme(const char * str);

#endif
