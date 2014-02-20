#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <ctype.h>

#include "parser_common.h"
#include "{{grammar.name}}_parser.h"

#define STDIN_BUF_SIZE 1024

typedef struct token_stream_t {

	TOKEN_T * token;
	struct token_stream_t * next;

} TOKEN_STREAM_T;
	
typedef enum token_field_e {
  TOKEN_FIELD_TERMINAL_E = 0x1,
  TOKEN_FIELD_LINE_E = 0x2,
  TOKEN_FIELD_COL_E = 0x4,
  TOKEN_FIELD_RESOURCE_E = 0x8,
  TOKEN_FIELD_SOURCE_STRING_E = 0x10,
  TOKEN_FIELD_ALL_E = 0x20 - 1,
  TOKEN_FIELD_NONE_E = 0,
  TOKEN_FIELD_INVALID_E = -1
} TOKEN_FIELD_E;

static TOKEN_FIELD_E str_to_token_field(char * str) {
  if ( !strcmp(str, "terminal") ) return TOKEN_FIELD_TERMINAL_E;
  else if ( !strcmp(str, "line") ) return TOKEN_FIELD_LINE_E;
  else if ( !strcmp(str, "col") ) return TOKEN_FIELD_COL_E;
  else if ( !strcmp(str, "resource") ) return TOKEN_FIELD_RESOURCE_E;
  else if ( !strcmp(str, "source_string") ) return TOKEN_FIELD_SOURCE_STRING_E;
  else return TOKEN_FIELD_INVALID_E;
}

static char * strdup2(const char *str)
{
  int n = strlen(str) + 1;
  char *dup = malloc(n);
  if(dup)
  {
    strcpy(dup, str);
  }
  return dup;
}

#define strdup strdup2

/* Start JSON parsing code */

/*  *
 * Copyright (C) 2012 James McLaughlin et al.  All rights reserved.
 * https://github.com/udp/json-parser
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#ifndef json_char
   #define json_char char
#endif

#ifdef __cplusplus

   extern "C"
   {

#endif

typedef struct
{
   unsigned long max_memory;
   int settings;

} json_settings;

#define json_relaxed_commas 1

typedef enum
{
   json_none,
   json_object,
   json_array,
   json_integer,
   json_double,
   json_string,
   json_boolean,
   json_null

} json_type;

extern const struct _json_value json_value_none;

typedef struct _json_value
{
   struct _json_value * parent;

   json_type type;

   union
   {
      int boolean;
      long integer;
      double dbl;

      struct
      {
         unsigned int length;
         json_char * ptr; /* null terminated */

      } string;

      struct
      {
         unsigned int length;

         struct
         {
            json_char * name;
            struct _json_value * value;

         } * values;

      } object;

      struct
      {
         unsigned int length;
         struct _json_value ** values;

      } array;

   } u;

   union
   {
      struct _json_value * next_alloc;
      void * object_mem;

   } _reserved;

} json_value;

json_value * json_parse
   (const json_char * json);

json_value * json_parse_ex
   (json_settings * settings, const json_char * json, char * error);

void json_value_free (json_value *);

#ifdef __cplusplus
   } /* extern "C" */
#endif

#ifdef _MSC_VER
   #ifndef _CRT_SECURE_NO_WARNINGS
      #define _CRT_SECURE_NO_WARNINGS
   #endif
#endif

#ifdef __cplusplus
   const struct _json_value json_value_none; /* zero-d by ctor */
#else
   const struct _json_value json_value_none = { 0 };
#endif

typedef unsigned short json_uchar;

static unsigned char hex_value (json_char c)
{
   if (c >= 'A' && c <= 'F')
      return (c - 'A') + 10;

   if (c >= 'a' && c <= 'f')
      return (c - 'a') + 10;

   if (c >= '0' && c <= '9')
      return c - '0';

   return 0xFF;
}

typedef struct
{
   json_settings settings;
   int first_pass;

   unsigned long used_memory;

   unsigned int uint_max;
   unsigned long ulong_max;

} json_state;

static void * json_alloc (json_state * state, unsigned long size, int zero)
{
   void * mem;

   if ((state->ulong_max - state->used_memory) < size)
      return 0;

   if (state->settings.max_memory
         && (state->used_memory += size) > state->settings.max_memory)
   {
      return 0;
   }

   if (! (mem = zero ? calloc (size, 1) : malloc (size)))
      return 0;

   return mem;
}

static int new_value
   (json_state * state, json_value ** top, json_value ** root, json_value ** alloc, json_type type)
{
   json_value * value;
   int values_size;

   if (!state->first_pass)
   {
      value = *top = *alloc;
      *alloc = (*alloc)->_reserved.next_alloc;

      if (!*root)
         *root = value;

      switch (value->type)
      {
         case json_array:

            if (! (value->u.array.values = (json_value **) json_alloc
               (state, value->u.array.length * sizeof (json_value *), 0)) )
            {
               return 0;
            }

            break;

         case json_object:

            values_size = sizeof (*value->u.object.values) * value->u.object.length;

            if (! ((*(void **) &value->u.object.values) = json_alloc
                  (state, values_size + ((unsigned long) value->u.object.values), 0)) )
            {
               return 0;
            }

            value->_reserved.object_mem = (*(char **) &value->u.object.values) + values_size;

            break;

         case json_string:

            if (! (value->u.string.ptr = (json_char *) json_alloc
               (state, (value->u.string.length + 1) * sizeof (json_char), 0)) )
            {
               return 0;
            }

            break;

         default:
            break;
      };

      value->u.array.length = 0;

      return 1;
   }

   value = (json_value *) json_alloc (state, sizeof (json_value), 1);

   if (!value)
      return 0;

   if (!*root)
      *root = value;

   value->type = type;
   value->parent = *top;

   if (*alloc)
      (*alloc)->_reserved.next_alloc = value;

   *alloc = *top = value;

   return 1;
}

#define e_off \
   ((int) (i - cur_line_begin))

#define whitespace \
   case '\n': ++ cur_line;  cur_line_begin = i; \
   case ' ': case '\t': case '\r'

#define string_add(b)  \
   do { if (!state.first_pass) string [string_length] = b;  ++ string_length; } while (0);

const static int
   flag_next = 1, flag_reproc = 2, flag_need_comma = 4, flag_seek_value = 8, flag_exponent = 16,
   flag_got_exponent_sign = 32, flag_escaped = 64, flag_string = 128, flag_need_colon = 256,
   flag_done = 512;

json_value * json_parse_ex (json_settings * settings, const json_char * json, char * error_buf)
{
   json_char error [128];
   unsigned int cur_line;
   const json_char * cur_line_begin, * i;
   json_value * top, * root, * alloc = 0;
   json_state state;
   int flags;

   error[0] = '\0';

   memset (&state, 0, sizeof (json_state));
   memcpy (&state.settings, settings, sizeof (json_settings));

   memset (&state.uint_max, 0xFF, sizeof (state.uint_max));
   memset (&state.ulong_max, 0xFF, sizeof (state.ulong_max));

   state.uint_max -= 8; /* limit of how much can be added before next check */
   state.ulong_max -= 8;

   for (state.first_pass = 1; state.first_pass >= 0; -- state.first_pass)
   {
      json_uchar uchar;
      unsigned char uc_b1, uc_b2, uc_b3, uc_b4;
      json_char * string;
      unsigned int string_length;

      top = root = 0;
      flags = flag_seek_value;

      cur_line = 1;
      cur_line_begin = json;

      for (i = json ;; ++ i)
      {
         json_char b = *i;

         if (flags & flag_done)
         {
            if (!b)
               break;

            switch (b)
            {
               whitespace:
                  continue;

               default:
                  sprintf (error, "%d:%d: Trailing garbage: `%c`", cur_line, e_off, b);
                  goto e_failed;
            };
         }

         if (flags & flag_string)
         {
            if (!b)
            {  sprintf (error, "Unexpected EOF in string (at %d:%d)", cur_line, e_off);
               goto e_failed;
            }

            if (string_length > state.uint_max)
               goto e_overflow;

            if (flags & flag_escaped)
            {
               flags &= ~ flag_escaped;

               switch (b)
               {
                  case 'b':  string_add ('\b');  break;
                  case 'f':  string_add ('\f');  break;
                  case 'n':  string_add ('\n');  break;
                  case 'r':  string_add ('\r');  break;
                  case 't':  string_add ('\t');  break;
                  case 'u':

                    if ((uc_b1 = hex_value (*++ i)) == 0xFF || (uc_b2 = hex_value (*++ i)) == 0xFF
                          || (uc_b3 = hex_value (*++ i)) == 0xFF || (uc_b4 = hex_value (*++ i)) == 0xFF)
                    {
                        sprintf (error, "Invalid character value `%c` (at %d:%d)", b, cur_line, e_off);
                        goto e_failed;
                    }

                    uc_b1 = uc_b1 * 16 + uc_b2;
                    uc_b2 = uc_b3 * 16 + uc_b4;

                    uchar = ((json_char) uc_b1) * 256 + uc_b2;

                    if (sizeof (json_char) >= sizeof (json_uchar) || (uc_b1 == 0 && uc_b2 <= 0x7F))
                    {
                       string_add ((json_char) uchar);
                       break;
                    }

                    if (uchar <= 0x7FF)
                    {
                        if (state.first_pass)
                           string_length += 2;
                        else
                        {  string [string_length ++] = 0xC0 | ((uc_b2 & 0xC0) >> 6) | ((uc_b1 & 0x3) << 3);
                           string [string_length ++] = 0x80 | (uc_b2 & 0x3F);
                        }

                        break;
                    }

                    if (state.first_pass)
                       string_length += 3;
                    else
                    {  string [string_length ++] = 0xE0 | ((uc_b1 & 0xF0) >> 4);
                       string [string_length ++] = 0x80 | ((uc_b1 & 0xF) << 2) | ((uc_b2 & 0xC0) >> 6);
                       string [string_length ++] = 0x80 | (uc_b2 & 0x3F);
                    }

                    break;

                  default:
                     string_add (b);
               };

               continue;
            }

            if (b == '\\')
            {
               flags |= flag_escaped;
               continue;
            }

            if (b == '"')
            {
               if (!state.first_pass)
                  string [string_length] = 0;

               flags &= ~ flag_string;
               string = 0;

               switch (top->type)
               {
                  case json_string:

                     top->u.string.length = string_length;
                     flags |= flag_next;

                     break;

                  case json_object:

                     if (state.first_pass)
                        (*(json_char **) &top->u.object.values) += string_length + 1;
                     else
                     {  
                        top->u.object.values [top->u.object.length].name
                           = (json_char *) top->_reserved.object_mem;

                        (*(json_char **) &top->_reserved.object_mem) += string_length + 1;
                     }

                     flags |= flag_seek_value | flag_need_colon;
                     continue;

                  default:
                     break;
               };
            }
            else
            {
               string_add (b);
               continue;
            }
         }

         if (flags & flag_seek_value)
         {
            switch (b)
            {
               whitespace:
                  continue;

               case ']':

                  if (top->type == json_array)
                     flags = (flags & ~ (flag_need_comma | flag_seek_value)) | flag_next;
                  else if (!state.settings.settings & json_relaxed_commas)
                  {  sprintf (error, "%d:%d: Unexpected ]", cur_line, e_off);
                     goto e_failed;
                  }

                  break;

               default:

                  if (flags & flag_need_comma)
                  {
                     if (b == ',')
                     {  flags &= ~ flag_need_comma;
                        continue;
                     }
                     else
                     {  sprintf (error, "%d:%d: Expected , before %c", cur_line, e_off, b);
                        goto e_failed;
                     }
                  }

                  if (flags & flag_need_colon)
                  {
                     if (b == ':')
                     {  flags &= ~ flag_need_colon;
                        continue;
                     }
                     else
                     {  sprintf (error, "%d:%d: Expected : before %c", cur_line, e_off, b);
                        goto e_failed;
                     }
                  }

                  flags &= ~ flag_seek_value;

                  switch (b)
                  {
                     case '{':

                        if (!new_value (&state, &top, &root, &alloc, json_object))
                           goto e_alloc_failure;

                        continue;

                     case '[':

                        if (!new_value (&state, &top, &root, &alloc, json_array))
                           goto e_alloc_failure;

                        flags |= flag_seek_value;
                        continue;

                     case '"':

                        if (!new_value (&state, &top, &root, &alloc, json_string))
                           goto e_alloc_failure;

                        flags |= flag_string;

                        string = top->u.string.ptr;
                        string_length = 0;

                        continue;

                     case 't':

                        if (*(++ i) != 'r' || *(++ i) != 'u' || *(++ i) != 'e')
                           goto e_unknown_value;

                        if (!new_value (&state, &top, &root, &alloc, json_boolean))
                           goto e_alloc_failure;

                        top->u.boolean = 1;

                        flags |= flag_next;
                        break;

                     case 'f':

                        if (*(++ i) != 'a' || *(++ i) != 'l' || *(++ i) != 's' || *(++ i) != 'e')
                           goto e_unknown_value;

                        if (!new_value (&state, &top, &root, &alloc, json_boolean))
                           goto e_alloc_failure;

                        flags |= flag_next;
                        break;

                     case 'n':

                        if (*(++ i) != 'u' || *(++ i) != 'l' || *(++ i) != 'l')
                           goto e_unknown_value;

                        if (!new_value (&state, &top, &root, &alloc, json_null))
                           goto e_alloc_failure;

                        flags |= flag_next;
                        break;

                     default:

                        if (isdigit (b) || b == '-')
                        {
                           if (!new_value (&state, &top, &root, &alloc, json_integer))
                              goto e_alloc_failure;

                           flags &= ~ (flag_exponent | flag_got_exponent_sign);

                           if (state.first_pass)
                              continue;

                           if (top->type == json_double)
                              top->u.dbl = strtod (i, (json_char **) &i);
                           else
                              top->u.integer = strtol (i, (json_char **) &i, 10);

                           flags |= flag_next | flag_reproc;
                        }
                        else
                        {  sprintf (error, "%d:%d: Unexpected %c when seeking value", cur_line, e_off, b);
                           goto e_failed;
                        }
                  };
            };
         }
         else
         {
            switch (top->type)
            {
            case json_object:
               
               switch (b)
               {
                  whitespace:
                     continue;

                  case '"':

                     if (flags & flag_need_comma && (!state.settings.settings & json_relaxed_commas))
                     {
                        sprintf (error, "%d:%d: Expected , before \"", cur_line, e_off);
                        goto e_failed;
                     }

                     flags |= flag_string;

                     string = (json_char *) top->_reserved.object_mem;
                     string_length = 0;

                     break;
                  
                  case '}':

                     flags = (flags & ~ flag_need_comma) | flag_next;
                     break;

                  case ',':

                     if (flags & flag_need_comma)
                     {
                        flags &= ~ flag_need_comma;
                        break;
                     }

                  default:

                     sprintf (error, "%d:%d: Unexpected `%c` in object", cur_line, e_off, b);
                     goto e_failed;
               };

               break;

            case json_integer:
            case json_double:

               if (isdigit (b))
                  continue;

               if (b == 'e' || b == 'E')
               {
                  if (!(flags & flag_exponent))
                  {
                     flags |= flag_exponent;
                     top->type = json_double;

                     continue;
                  }
               }
               else if (b == '+' || b == '-')
               {
                  if (flags & flag_exponent && !(flags & flag_got_exponent_sign))
                  {
                     flags |= flag_got_exponent_sign;
                     continue;
                  }
               }
               else if (b == '.' && top->type == json_integer)
               {
                  top->type = json_double;
                  continue;
               }

               flags |= flag_next | flag_reproc;
               break;

            default:
               break;
            };
         }

         if (flags & flag_reproc)
         {
            flags &= ~ flag_reproc;
            -- i;
         }

         if (flags & flag_next)
         {
            flags = (flags & ~ flag_next) | flag_need_comma;

            if (!top->parent)
            {
               /* root value done */

               flags |= flag_done;
               continue;
            }

            if (top->parent->type == json_array)
               flags |= flag_seek_value;
               
            if (!state.first_pass)
            {
               json_value * parent = top->parent;

               switch (parent->type)
               {
                  case json_object:

                     parent->u.object.values
                        [parent->u.object.length].value = top;

                     break;

                  case json_array:

                     parent->u.array.values
                           [parent->u.array.length] = top;

                     break;

                  default:
                     break;
               };
            }

            if ( (++ top->parent->u.array.length) > state.uint_max)
               goto e_overflow;

            top = top->parent;

            continue;
         }
      }

      alloc = root;
   }

   return root;

e_unknown_value:

   sprintf (error, "%d:%d: Unknown value", cur_line, e_off);
   goto e_failed;

e_alloc_failure:

   strcpy (error, "Memory allocation failure");
   goto e_failed;

e_overflow:

   sprintf (error, "%d:%d: Too long (caught overflow)", cur_line, e_off);
   goto e_failed;

e_failed:

   if (error_buf)
   {
      if (*error)
         strcpy (error_buf, error);
      else
         strcpy (error_buf, "Unknown error");
   }

   if (state.first_pass)
      alloc = root;

   while (alloc)
   {
      top = alloc->_reserved.next_alloc;
      free (alloc);
      alloc = top;
   }

   if (!state.first_pass)
      json_value_free (root);

   return 0;
}

json_value * json_parse (const json_char * json)
{
   json_settings settings;
   memset (&settings, 0, sizeof (json_settings));

   return json_parse_ex (&settings, json, 0);
}

void json_value_free (json_value * value)
{
   json_value * cur_value;

   if (!value)
      return;

   value->parent = 0;

   while (value)
   {
      switch (value->type)
      {
         case json_array:

            if (!value->u.array.length)
            {
               free (value->u.array.values);
               break;
            }

            value = value->u.array.values [-- value->u.array.length];
            continue;

         case json_object:

            if (!value->u.object.length)
            {
               free (value->u.object.values);
               break;
            }

            value = value->u.object.values [-- value->u.object.length].value;
            continue;

         case json_string:

            free (value->u.string.ptr);
            break;

         default:
            break;
      };

      cur_value = value;
      value = value->parent;
      free (cur_value);
   }
}

/* End JSON parsing code */

#define BUFFER_SIZE 256

int
read_file( char ** content, FILE * fp )
{
  int content_len = BUFFER_SIZE * 4;
  char buf[BUFFER_SIZE];
  int bytes, total_bytes_read = 0;

  *content = calloc(content_len + 1, sizeof(char));

  while ( (bytes = fread(buf, sizeof(char), BUFFER_SIZE, fp)) != 0 )
  {
    if (content_len - total_bytes_read < BUFFER_SIZE) {
      content_len *= 2;
      *content = realloc(*content, (content_len * sizeof(char)) + 1);
    }

    memcpy(*content + total_bytes_read, buf, bytes);
    total_bytes_read += bytes;
  }

  *(*content + total_bytes_read) = '\0';
  return total_bytes_read;
}

TOKEN_LIST_T *
get_tokens(char * grammar, char * json_input, TOKEN_LIST_T * token_list) {
  TOKEN_T * tokens;
  TOKEN_T end_of_stream;
  int i, j, ntokens;
  json_value * json;
  TOKEN_FIELD_E field, field_mask;
  int (*terminal_str_to_id)(const char *);

  if ( strcmp("{{grammar.name}}", grammar) == 0 ) {
    terminal_str_to_id = {{grammar.name}}_str_to_morpheme;
  }

  memset(&end_of_stream, 0, sizeof(TOKEN_T));
  end_of_stream.terminal = calloc(1, sizeof(TERMINAL_T));
  end_of_stream.terminal->id = -1;

  json = json_parse(json_input);

  if ( json == NULL ) {
    fprintf(stderr, "get_tokens(): Invalid JSON input\n");
    exit(-1);
  }

  if ( json->type != json_array ) {
    fprintf(stderr, "get_tokens(): JSON input should be an array of tokens\n");
    exit(-1);
  }

  ntokens = json->u.array.length;
  tokens = calloc(ntokens+1, sizeof(TOKEN_T));
  memcpy(&tokens[ntokens], &end_of_stream, sizeof(TOKEN_T));

  for ( i = 0; i < json->u.array.length; i++ ) {

    json_value * json_token = json->u.array.values[i];
    TOKEN_T * token = &tokens[i];
    token->terminal = calloc(1, sizeof(TERMINAL_T));

    if ( json_token->type != json_object ) {
      fprintf(stderr, "get_tokens(): JSON input should be an array of tokens\n");
      exit(-1);
    }

    for ( j = 0, field_mask = TOKEN_FIELD_NONE_E; j < json_token->u.object.length; j++ ) {
      char * name = json_token->u.object.values[j].name;
      json_value * value = json_token->u.object.values[j].value;
      field = str_to_token_field(name);

      if ( field == TOKEN_FIELD_INVALID_E ) {
        fprintf(stderr, "'%s' field is invalid for a token", name);
        exit(-1);
      } else if ( field & (TOKEN_FIELD_TERMINAL_E | TOKEN_FIELD_RESOURCE_E | TOKEN_FIELD_SOURCE_STRING_E) && (value == NULL || value->type != json_string) ) {
        fprintf(stderr, "'%s' field must have a string value", name); 
        exit(-1);
      } else if ( field == TOKEN_FIELD_TERMINAL_E && terminal_str_to_id(value->u.string.ptr) == -1 ) {
        fprintf(stderr, "'%s' field does not have a valid terminal identifier (%s)", name, value->u.string.ptr); 
        exit(-1);
      } else if ( field & (TOKEN_FIELD_COL_E | TOKEN_FIELD_LINE_E) && (value == NULL || (value->type != json_string && value->type != json_integer)) ) {
        fprintf(stderr, "'%s' field must have a string or integer value", name); 
        exit(-1);
      }

      field_mask |= field;
    }

    if ( (field_mask & TOKEN_FIELD_TERMINAL_E) == 0 ) {
      fprintf(stderr, "'terminal' field must be specified for all tokens");
      exit(-1);
    }

    for ( j = 0, field_mask = TOKEN_FIELD_NONE_E; j < json_token->u.object.length; j++ ) {
      char * name = json_token->u.object.values[j].name;
      json_value * value = json_token->u.object.values[j].value;
      field = str_to_token_field(name);

      switch ( field ) {
        case TOKEN_FIELD_COL_E:
          if ( value->type == json_string ) {
            token->colno = atoi(value->u.string.ptr);
          } else if ( value->type == json_integer ) {
            token->colno = value->u.integer;
          }
          break;

        case TOKEN_FIELD_LINE_E:
          if ( value->type == json_string ) {
            token->lineno = atoi(value->u.string.ptr);
          } else if ( value->type == json_integer ) {
            token->lineno = value->u.integer;
          }
          break;

        case TOKEN_FIELD_TERMINAL_E:
          token->terminal->string = strdup((const char *) value->u.string.ptr);
          token->terminal->id = terminal_str_to_id(value->u.string.ptr);
          break;

        case TOKEN_FIELD_RESOURCE_E:
          token->resource = strdup((const char *) value->u.string.ptr);
          break;

        case TOKEN_FIELD_SOURCE_STRING_E:
          token->source_string = strdup((const char *) value->u.string.ptr);
          break;

        default:
          fprintf(stderr, "Unknown error\n");
          exit(-1);
      }
    }
  }

  token_list->tokens = tokens;
  token_list->ntokens = ntokens;
  token_list->current = tokens[0].terminal->id;
  token_list->current_index = -1;
  return token_list;
}

int
main(int argc, char * argv[])
{
  PARSE_TREE_T * parse_tree;
  PARSER_CONTEXT_T * ctx;
  ABSTRACT_SYNTAX_TREE_T * abstract_syntax_tree;
  TOKEN_LIST_T token_list;
  char * str;
  int i, j, rval;
  char * stdin_content;
  int stdin_len;
  FILE * fp;

  if ( argc < 3 )
  {
    fprintf(stderr, "Usage: %s <parsetree,ast> <tokens_file>\n", argv[0]);
    exit(-1);
  }

  fp = fopen(argv[2], "r");  
  stdin_len = read_file( &stdin_content, fp );

  get_tokens("{{grammar.name}}", stdin_content, &token_list);
  ctx = {{grammar.name}}_parser_init(&token_list);
  parse_tree = {{grammar.name}}_parse(&token_list, -1, ctx);
  abstract_syntax_tree = {{grammar.name}}_ast(parse_tree);

  if ( argc >= 3 && !strcmp(argv[1], "ast") ) {
    str = ast_to_string(abstract_syntax_tree, ctx);
  }
  else {
    str = parsetree_to_string(parse_tree, ctx);
  }

  free_parse_tree(parse_tree);
  free_ast(abstract_syntax_tree);

  if ( ctx->syntax_errors ) {
    rval = 1;
    printf("%s\n", ctx->syntax_errors->message);
    /*for ( error = ctx->syntax_errors; error; error = error->next )
    {
      printf("%s\n", error->message);
    }*/
  }
  else
  {
    rval = 0;
    printf("%s", str);
  }

  {{grammar.name}}_parser_exit(ctx);

  return rval;
}
