#ifndef _GRAMMAR_H
#define _GRAMMAR_H

#include <unicode/uchar.h>

#ifdef __cplusplus
extern "C" {
#endif

%%DECL_NONTERMINALS%%

%%DECL_TERMINALS%%

typedef enum grammar_atom_type_e {

  NONTERMINAL,
  TERMINAL

} GRAMMAR_ATOM_TYPE_E;

typedef struct parse_syntax_error_t {

  UChar * message;
  struct grammar_token_t * token;

} GRAMMAR_SYNTAX_ERROR_T;

typedef struct grammar_token_t {

  enum grammar_terminal_e type;
  UChar * text;
  int lineno;
  int colno;

} GRAMMAR_TOKEN_T;

typedef struct grammar_nonterminal_t {

  enum grammar_atom_type_e type;
  enum grammar_nonterminal_e nonterminal;
  union grammar_atom_u ** children;
  int nchildren;
  
} GRAMMAR_NONTERMINAL_T;

typedef struct grammar_terminal_t {

  enum grammar_atom_type_e type;
  GRAMMAR_TOKEN_T * token;

} GRAMMAR_TERMINAL_T;

typedef struct grammar_atom_t {

  enum grammar_atom_type_e type;

} GRAMMAR_ATOM_T;

typedef union grammar_atom_u {
  
  struct grammar_nonterminal_t nonterminal;
  struct grammar_terminal_t terminal;
  struct grammar_atom_t atom;

} GRAMMAR_ATOM_U;

typedef struct parse_state_t {

  GRAMMAR_TOKEN_T * token;
  GRAMMAR_SYNTAX_ERROR_T * syntaxError;

  GRAMMAR_TERMINAL_T * (*_ZsGrammar_Expect)( struct parse_state_t *, GRAMMAR_TERMINAL_E );
  void * (*_ZsGrammar_Calloc)( struct parse_state_t *, int count, size_t size );

} PARSE_STATE_T;

%%C_DECL_PUBLIC_FUNCTIONS%%
char * ZsGrammar_TerminalToString( GRAMMAR_TERMINAL_E terminal );
char * ZsGrammar_NonTerminalToString( GRAMMAR_NONTERMINAL_E nonterminal );

#ifdef __cplusplus
}
#endif

#endif
