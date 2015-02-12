#ifndef __{{prefix.upper()}}_LEXER_H
#define __{{prefix.upper()}}_LEXER_H

#include "parser_common.h"

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

TOKEN_T ** {{prefix}}lex(char * string, char * resource, char * error);

#endif
