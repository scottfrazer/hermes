#include "grammar.h"

#define TERMINAL(type, state) (GRAMMAR_ATOM_U *) state->_ZsGrammar_Expect( state, type ); \
if(state->syntaxError) return NULL

#define NONTERMINAL(func, state) (GRAMMAR_ATOM_U *) func(state);\
if(state->syntaxError) return NULL

static int _ZsGrammar_GetRule( int N, int T );
static GRAMMAR_NONTERMINAL_T * _ZsGrammar_NonTerminal ( PARSE_STATE_T * state, GRAMMAR_ATOM_U ** children, int nchildren, GRAMMAR_NONTERMINAL_E nt_type );

%%INIT%%

static int
_ZsGrammar_GetRule( int N, int T )
{
  return _ZsGrammar_ParseTable[N][T];
}

static GRAMMAR_NONTERMINAL_T * 
_ZsGrammar_NonTerminal ( PARSE_STATE_T * state, GRAMMAR_ATOM_U ** children, int nchildren, GRAMMAR_NONTERMINAL_E nt_type )
{
  GRAMMAR_NONTERMINAL_T * nonterminal = state->_ZsGrammar_Calloc( state, 1, sizeof( GRAMMAR_NONTERMINAL_T ) );
  nonterminal->type = NONTERMINAL;
  nonterminal->nonterminal = nt_type;
  nonterminal->children = children;
  nonterminal->nchildren = nchildren;
  return nonterminal;
}

char *
ZsGrammar_TerminalToString( GRAMMAR_TERMINAL_E terminal )
{
  if ( terminal >= _ZsGrammar_nTerminals )
    return "N/A";
  return _ZsGrammar_TerminalStr[terminal];
}

char *
ZsGrammar_NonTerminalToString( GRAMMAR_NONTERMINAL_E nonterminal )
{
  if ( nonterminal >= _ZsGrammar_nNonTerminals )
    return "N/A";
  return _ZsGrammar_NonTerminalStr[nonterminal];
}

%%PARSER%%
%%PUBLIC_FUNCTION_DEFINITIONS%%
%%MAIN%%