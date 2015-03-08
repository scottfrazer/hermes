{% from hermes.grammar import * %}

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

{% if add_main %}
#include <fcntl.h>
{% endif %}

{% if lexer %}
#include <pcre.h>
{% endif %}

#include "{{prefix.lower()}}parser.h"

#define TRUE 1
#define FALSE 0

/* Section: utility functions */

#define READ_FILE_BUFFER_SIZE 256

static int
read_file( char ** content, FILE * fp )
{
    int content_len = READ_FILE_BUFFER_SIZE * 4;
    char buf[READ_FILE_BUFFER_SIZE];
    int bytes, total_bytes_read = 0;

    *content = calloc(content_len + 1, sizeof(char));

    while ( (bytes = fread(buf, sizeof(char), READ_FILE_BUFFER_SIZE, fp)) != 0 ) {
        if (content_len - total_bytes_read < READ_FILE_BUFFER_SIZE) {
            content_len *= 2;
            *content = realloc(*content, (content_len * sizeof(char)) + 1);
        }

        memcpy(*content + total_bytes_read, buf, bytes);
        total_bytes_read += bytes;
    }

    *(*content + total_bytes_read) = '\0';
    return total_bytes_read;
}

static char *
_get_indent_str(int length)
{
  char * str = malloc(length + 1 * sizeof(char));
  memset(str, ' ', length);
  str[length] = '\0';
  return str;
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

static void
_prepend(char * s, const char * t)
{
    size_t len = strlen(t);
    size_t i;

    memmove(s + len, s, strlen(s) + 1);

    for (i = 0; i < len; ++i) {
        s[i] = t[i];
    }
}

/* Section: Base64 encoding/decoding */

#define BASE64_OUTPUT_TOO_SMALL 1
#define BASE64_INPUT_EQUALS_OUTPUT 2
#define BASE64_INPUT_MALFORMED 3
#define BASE64_NULL_OUTPUT 4

static char * encoding_table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
static int mod_table[] = {0, 2, 1};

static int
decode_byte(char c)
{
    if (c >= 'A' && c <= 'Z') return c - 65; /* 0 - 25 */
    if (c >= 'a' && c <= 'z') return c - 71; /* 26 - 51 */
    if (c >= '0' && c <= '9')  return c + 4;  /* 52 - 61 */
    if (c == '+')             return 62;
    if (c == '/')             return 63;
    return 0;
}

static int
base64_encode(const char * input, size_t input_length, char * output, size_t output_length)
{
    int i, j, pad;
    size_t encoded_length = 4 * ((input_length + 2) / 3);
    if (encoded_length + 1 > output_length) return BASE64_OUTPUT_TOO_SMALL;
    if (output == NULL) return BASE64_NULL_OUTPUT;
    if (input == output) return BASE64_INPUT_EQUALS_OUTPUT;

    for (i = 0, j = 0; i < input_length;) {
        int octet_a = i < input_length ? (unsigned char) input[i++] : 0;
        int octet_b = i < input_length ? (unsigned char) input[i++] : 0;
        int octet_c = i < input_length ? (unsigned char) input[i++] : 0;
        int triple = (octet_a << 0x10) + (octet_b << 0x08) + octet_c;
        output[j++] = encoding_table[(triple >> 3 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 2 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 1 * 6) & 0x3F];
        output[j++] = encoding_table[(triple >> 0 * 6) & 0x3F];
    }


    for (i = 0, pad = mod_table[input_length % 3], j -= pad; i < pad; i++) {
        output[j++] = '=';
    }

    output[j++] = '\0';
    return 0;
}

static int
base64_decode(const char * input, char * output, size_t output_length, size_t * decoded_length)
{
    int input_length = strlen(input);

    if (input_length % 4 != 0) {
        return BASE64_INPUT_MALFORMED;
    }

    *decoded_length = input_length / 4 * 3;
    if (input[input_length - 1] == '=') (*decoded_length)--;
    if (input[input_length - 2] == '=') (*decoded_length)--;

    if (*decoded_length > output_length) {
        return BASE64_OUTPUT_TOO_SMALL;
    }

    if (output == NULL) {
        return BASE64_NULL_OUTPUT;
    }

    for (int i = 0, j = 0; i < input_length;) {
        int sextet_a = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_b = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_c = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int sextet_d = input[i] == '=' ? 0 : decode_byte(input[i]);i++;
        int triple = (sextet_a << 3 * 6) + (sextet_b << 2 * 6) + (sextet_c << 1 * 6) + (sextet_d << 0 * 6);
        if (j < *decoded_length) output[j++] = (triple >> 2 * 8) & 0xFF;
        if (j < *decoded_length) output[j++] = (triple >> 1 * 8) & 0xFF;
        if (j < *decoded_length) output[j++] = (triple >> 0 * 8) & 0xFF;
    }

    return 0;
}

/* Section: JSON Parsing */

{% if add_main %}
#ifndef json_char
   #define json_char char
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
   unsigned long max_memory;
   int settings;
} json_settings;

#define json_relaxed_commas 1

typedef enum {
   json_none,
   json_object,
   json_array,
   json_integer,
   json_double,
   json_string,
   json_boolean,
   json_null
} json_type;

/*extern const struct _json_value json_value_none;*/

typedef struct _json_value {
   struct _json_value * parent;
   json_type type;

   union {
      int boolean;
      long integer;
      double dbl;

      struct {
         unsigned int length;
         json_char * ptr; /* null terminated */
      } string;

      struct {
         unsigned int length;
         struct {
            json_char * name;
            struct _json_value * value;
         } * values;
      } object;

      struct {
         unsigned int length;
         struct _json_value ** values;
      } array;
   } u;

   union {
      struct _json_value * next_alloc;
      void * object_mem;
   } _reserved;

} json_value;

#ifdef __cplusplus
} /* extern "C" */
#endif

#ifdef _MSC_VER
   #ifndef _CRT_SECURE_NO_WARNINGS
      #define _CRT_SECURE_NO_WARNINGS
   #endif
#endif

/*
#ifdef __cplusplus
   const struct _json_value json_value_none; // zero-d by ctor
#else
   const struct _json_value json_value_none = { 0 };
#endif
*/

typedef unsigned short json_uchar;

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

typedef struct {
    json_settings settings;
    int first_pass;

    unsigned long used_memory;

    unsigned int uint_max;
    unsigned long ulong_max;

} json_state;

static void json_value_free (json_value * value);
static json_value * json_parse_ex (json_settings * settings, const json_char * json, char * error_buf);

static unsigned char
hex_value (json_char c)
{
    if (c >= 'A' && c <= 'F')
        return (c - 'A') + 10;

    if (c >= 'a' && c <= 'f')
        return (c - 'a') + 10;

    if (c >= '0' && c <= '9')
        return c - '0';

    return 0xFF;
}

static void *
json_alloc (json_state * state, unsigned long size, int zero)
{
    void * mem;

    if ((state->ulong_max - state->used_memory) < size)
        return 0;

    if (state->settings.max_memory
            && (state->used_memory += size) > state->settings.max_memory) {
        return 0;
    }

    if (! (mem = zero ? calloc (size, 1) : malloc (size)))
        return 0;

    return mem;
}

static int
new_value(json_state * state, json_value ** top, json_value ** root, json_value ** alloc, json_type type)
{
    json_value * value;
    int values_size;

    if (!state->first_pass) {
        value = *top = *alloc;
        *alloc = (*alloc)->_reserved.next_alloc;

        if (!*root)
            *root = value;

        switch (value->type) {
        case json_array:

            if (! (value->u.array.values = (json_value **) json_alloc
                                           (state, value->u.array.length * sizeof (json_value *), 0)) ) {
                return 0;
            }

            break;

        case json_object:

            values_size = sizeof (*value->u.object.values) * value->u.object.length;

            if (! ((*(void **) &value->u.object.values) = json_alloc
                    (state, values_size + ((unsigned long) value->u.object.values), 0)) ) {
                return 0;
            }

            value->_reserved.object_mem = (*(char **) &value->u.object.values) + values_size;

            break;

        case json_string:

            if (! (value->u.string.ptr = (json_char *) json_alloc
                                         (state, (value->u.string.length + 1) * sizeof (json_char), 0)) ) {
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

static json_value *
json_parse_ex (json_settings * settings, const json_char * json, char * error_buf)
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

    for (state.first_pass = 1; state.first_pass >= 0; -- state.first_pass) {
        json_uchar uchar;
        unsigned char uc_b1, uc_b2, uc_b3, uc_b4;
        json_char * string;
        unsigned int string_length;

        top = root = 0;
        flags = flag_seek_value;

        cur_line = 1;
        cur_line_begin = json;

        for (i = json ;; ++ i) {
            json_char b = *i;

            if (flags & flag_done) {
                if (!b)
                    break;

                switch (b) {
whitespace:
                    continue;

                default:
                    sprintf (error, "%d:%d: Trailing garbage: `%c`", cur_line, e_off, b);
                    goto e_failed;
                };
            }

            if (flags & flag_string) {
                if (!b) {
                    sprintf (error, "Unexpected EOF in string (at %d:%d)", cur_line, e_off);
                    goto e_failed;
                }

                if (string_length > state.uint_max)
                    goto e_overflow;

                if (flags & flag_escaped) {
                    flags &= ~ flag_escaped;

                    switch (b) {
                    case 'b':
                        string_add ('\b');
                        break;
                    case 'f':
                        string_add ('\f');
                        break;
                    case 'n':
                        string_add ('\n');
                        break;
                    case 'r':
                        string_add ('\r');
                        break;
                    case 't':
                        string_add ('\t');
                        break;
                    case 'u':

                        if ((uc_b1 = hex_value (*++ i)) == 0xFF || (uc_b2 = hex_value (*++ i)) == 0xFF
                                || (uc_b3 = hex_value (*++ i)) == 0xFF || (uc_b4 = hex_value (*++ i)) == 0xFF) {
                            sprintf (error, "Invalid character value `%c` (at %d:%d)", b, cur_line, e_off);
                            goto e_failed;
                        }

                        uc_b1 = uc_b1 * 16 + uc_b2;
                        uc_b2 = uc_b3 * 16 + uc_b4;

                        uchar = ((json_char) uc_b1) * 256 + uc_b2;

                        if (sizeof (json_char) >= sizeof (json_uchar) || (uc_b1 == 0 && uc_b2 <= 0x7F)) {
                            string_add ((json_char) uchar);
                            break;
                        }

                        if (uchar <= 0x7FF) {
                            if (state.first_pass)
                                string_length += 2;
                            else {
                                string [string_length ++] = 0xC0 | ((uc_b2 & 0xC0) >> 6) | ((uc_b1 & 0x3) << 3);
                                string [string_length ++] = 0x80 | (uc_b2 & 0x3F);
                            }

                            break;
                        }

                        if (state.first_pass)
                            string_length += 3;
                        else {
                            string [string_length ++] = 0xE0 | ((uc_b1 & 0xF0) >> 4);
                            string [string_length ++] = 0x80 | ((uc_b1 & 0xF) << 2) | ((uc_b2 & 0xC0) >> 6);
                            string [string_length ++] = 0x80 | (uc_b2 & 0x3F);
                        }

                        break;

                    default:
                        string_add (b);
                    };

                    continue;
                }

                if (b == '\\') {
                    flags |= flag_escaped;
                    continue;
                }

                if (b == '"') {
                    if (!state.first_pass)
                        string [string_length] = 0;

                    flags &= ~ flag_string;
                    string = 0;

                    switch (top->type) {
                    case json_string:

                        top->u.string.length = string_length;
                        flags |= flag_next;

                        break;

                    case json_object:

                        if (state.first_pass)
                            (*(json_char **) &top->u.object.values) += string_length + 1;
                        else {
                            top->u.object.values [top->u.object.length].name
                                = (json_char *) top->_reserved.object_mem;

                            (*(json_char **) &top->_reserved.object_mem) += string_length + 1;
                        }

                        flags |= flag_seek_value | flag_need_colon;
                        continue;

                    default:
                        break;
                    };
                } else {
                    string_add (b);
                    continue;
                }
            }

            if (flags & flag_seek_value) {
                switch (b) {
whitespace:
                    continue;

                case ']':

                    if (top->type == json_array)
                        flags = (flags & ~ (flag_need_comma | flag_seek_value)) | flag_next;
                    else if (!state.settings.settings & json_relaxed_commas) {
                        sprintf (error, "%d:%d: Unexpected ]", cur_line, e_off);
                        goto e_failed;
                    }

                    break;

                default:

                    if (flags & flag_need_comma) {
                        if (b == ',') {
                            flags &= ~ flag_need_comma;
                            continue;
                        } else {
                            sprintf (error, "%d:%d: Expected , before %c", cur_line, e_off, b);
                            goto e_failed;
                        }
                    }

                    if (flags & flag_need_colon) {
                        if (b == ':') {
                            flags &= ~ flag_need_colon;
                            continue;
                        } else {
                            sprintf (error, "%d:%d: Expected : before %c", cur_line, e_off, b);
                            goto e_failed;
                        }
                    }

                    flags &= ~ flag_seek_value;

                    switch (b) {
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

                        if (isdigit (b) || b == '-') {
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
                        } else {
                            sprintf (error, "%d:%d: Unexpected %c when seeking value", cur_line, e_off, b);
                            goto e_failed;
                        }
                    };
                };
            } else {
                switch (top->type) {
                case json_object:

                    switch (b) {
whitespace:
                        continue;

                    case '"':

                        if (flags & flag_need_comma && (!state.settings.settings & json_relaxed_commas)) {
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

                        if (flags & flag_need_comma) {
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

                    if (b == 'e' || b == 'E') {
                        if (!(flags & flag_exponent)) {
                            flags |= flag_exponent;
                            top->type = json_double;

                            continue;
                        }
                    } else if (b == '+' || b == '-') {
                        if (flags & flag_exponent && !(flags & flag_got_exponent_sign)) {
                            flags |= flag_got_exponent_sign;
                            continue;
                        }
                    } else if (b == '.' && top->type == json_integer) {
                        top->type = json_double;
                        continue;
                    }

                    flags |= flag_next | flag_reproc;
                    break;

                default:
                    break;
                };
            }

            if (flags & flag_reproc) {
                flags &= ~ flag_reproc;
                -- i;
            }

            if (flags & flag_next) {
                flags = (flags & ~ flag_next) | flag_need_comma;

                if (!top->parent) {
                    /* root value done */

                    flags |= flag_done;
                    continue;
                }

                if (top->parent->type == json_array)
                    flags |= flag_seek_value;

                if (!state.first_pass) {
                    json_value * parent = top->parent;

                    switch (parent->type) {
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

    if (error_buf) {
        if (*error)
            strcpy (error_buf, error);
        else
            strcpy (error_buf, "Unknown error");
    }

    if (state.first_pass)
        alloc = root;

    while (alloc) {
        top = alloc->_reserved.next_alloc;
        free (alloc);
        alloc = top;
    }

    if (!state.first_pass)
        json_value_free (root);

    return 0;
}

static json_value *
json_parse (const json_char * json)
{
    json_settings settings;
    memset (&settings, 0, sizeof (json_settings));

    return json_parse_ex (&settings, json, 0);
}

static void
json_value_free (json_value * value)
{
    json_value * cur_value;

    if (!value)
        return;

    value->parent = 0;

    while (value) {
        switch (value->type) {
        case json_array:

            if (!value->u.array.length) {
                free (value->u.array.values);
                break;
            }

            value = value->u.array.values [-- value->u.array.length];
            continue;

        case json_object:

            if (!value->u.object.length) {
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

{% endif %}

/* Section: AST and ParseTree functions */

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_list( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  AST_LIST_T * lnode, * tail, * ast_list;
  ABSTRACT_SYNTAX_TREE_T * this, * next;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  int offset, i;

  ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
  ast->type = AST_NODE_TYPE_LIST;
  ast->object = NULL;

  lnode = ast_list = tail = NULL;

  if ( tree->nchildren == 0 )
    return ast;

  if ( !strcmp(tree->list, "slist") || !strcmp(tree->list, "nlist") )
  {
    offset = (tree->children[0].object == tree->listSeparator) ? 1 : 0;
    this = {{prefix}}parsetree_node_to_ast(&tree->children[offset]);
    next = {{prefix}}parsetree_node_to_ast(&tree->children[offset + 1]);

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

    if ( next ) free(next);
  }
  else if ( !strcmp(tree->list, "otlist") )
  {
    this = {{prefix}}parsetree_node_to_ast(&tree->children[0]);
    next = {{prefix}}parsetree_node_to_ast(&tree->children[1]);
    if ( tree->children[0].object == tree->listSeparator )
    {
      ast_list = (AST_LIST_T *) next->object;
    }
    else
    {
      ast_list = calloc(1, sizeof(AST_LIST_T));
      ast_list->tree = this;
      ast_list->next = (AST_LIST_T *) next->object;
    }
  }
  else if ( !strcmp(tree->list, "tlist") )
  {
    this = {{prefix}}parsetree_node_to_ast(&tree->children[0]);
    next = {{prefix}}parsetree_node_to_ast(&tree->children[2]);

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

    if ( next ) free(next);
  }
  else if ( !strcmp(tree->list, "mlist") )
  {
    for ( i = 0; i < tree->nchildren - 1; i++ )
    {
      lnode = calloc(1, sizeof(AST_LIST_T));
      lnode->tree = {{prefix}}parsetree_node_to_ast(&tree->children[i]);

      if ( ast_list == NULL )
      {
        ast_list = tail = lnode;
        continue;
      }

      tail->next = (AST_LIST_T *) lnode;
      tail = tail->next;
    }

    next = {{prefix}}parsetree_node_to_ast(&tree->children[tree->nchildren - 1]);

    if ( next == NULL ) tail->next = NULL;
    else tail->next = (AST_LIST_T *) next->object;
  }

  ast->object = (AST_NODE_U *) ast_list;
  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_expr( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object, * first;
  AST_OBJECT_T * ast_object;
  PARSETREE_TO_AST_CONVERSION_T * ast_converter = tree->ast_converter;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) ast_converter->object;
  AST_RETURN_INDEX_T * ast_return_index = (AST_RETURN_INDEX_T *) ast_converter->object;
  PARSE_TREE_NODE_T * child;
  int index, i;

  if ( tree->ast_converter->type == AST_RETURN_INDEX )
  {
    ast = {{prefix}}parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( tree->ast_converter->type == AST_CREATE_OBJECT )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name) + 1, sizeof(char));
    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));

    strcpy(ast_object->name, ast_object_spec->name);
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
        return {{prefix}}parsetree_node_to_ast( &tree->children[0] );
      }
      else
      {
        child = &tree->children[index];
      }

      ast_object->children[i].tree = {{prefix}}parsetree_node_to_ast(child);
    }

    return ast;
  }

  return ast;
}

static ABSTRACT_SYNTAX_TREE_T *
__parsetree_node_to_ast_normal( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  AST_OBJECT_T * ast_object;
  PARSE_TREE_T * tree = (PARSE_TREE_T *) node->object;
  PARSETREE_TO_AST_CONVERSION_TYPE_E ast_conversion_type;
  AST_OBJECT_SPECIFICATION_T * ast_object_spec;
  AST_RETURN_INDEX_T * ast_return_index;
  AST_RETURN_INDEX_T default_action = { .index = 0 };
  int i;

  if ( tree->ast_converter )
  {
    ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) tree->ast_converter->object;
    ast_return_index = (AST_RETURN_INDEX_T *) tree->ast_converter->object;
    ast_conversion_type = tree->ast_converter->type;
  }
  else
  {
    ast_object_spec = (AST_OBJECT_SPECIFICATION_T *) NULL;
    ast_return_index = (AST_RETURN_INDEX_T *) &default_action;
    ast_conversion_type = AST_RETURN_INDEX;
  }

  if ( ast_conversion_type == AST_RETURN_INDEX )
  {
    ast = {{prefix}}parsetree_node_to_ast( &tree->children[ast_return_index->index] );
  }

  if ( ast_conversion_type == AST_CREATE_OBJECT )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast_object = calloc(1, sizeof(AST_OBJECT_T));
    ast_object->name = calloc(strlen(ast_object_spec->name)+1, sizeof(char));
    ast_object->children = calloc(ast_object_spec->nattrs, sizeof(ABSTRACT_SYNTAX_TREE_ATTR_T));

    strcpy( ast_object->name, ast_object_spec->name );
    ast_object->nchildren = ast_object_spec->nattrs;

    ast->object = (AST_NODE_U *) ast_object;
    ast->type = AST_NODE_TYPE_OBJECT;

    for ( i = 0; i < ast_object_spec->nattrs; i++ )
    {
      ast_object->children[i].name = ast_object_spec->attrs[i].name;
      ast_object->children[i].tree = {{prefix}}parsetree_node_to_ast(&tree->children[ast_object_spec->attrs[i].index]);
    }
  }

  return ast;
}

static int
token_to_string_bytes(TOKEN_T * token)
{
  /* format: "<identifier (line 0 col 0) ``>" */
  int source_string_len = token->source_string ? strlen(token->source_string) : 5;
  return 1 + strlen({{prefix}}morpheme_to_str(token->terminal->id)) + 7 + 5 + 5 + 5 + 3 + source_string_len + 2;
}

static int
_parsetree_to_string_bytes( PARSE_TREE_NODE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_T * tree;
  int bytes, i;

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      /* format: "(nonterminal: )" */
      return 4 + strlen(ctx->morpheme_to_str(tree->nonterminal));
    }
    else
    {
      bytes = (5 + indent + strlen(ctx->morpheme_to_str(tree->nonterminal)));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        bytes += 2 + indent + _parsetree_to_string_bytes(&tree->children[i], indent + 2, ctx);
      }
      bytes += (tree->nchildren - 1) * 2;
      return bytes;
    }
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    return 2 + token_to_string_bytes((TOKEN_T *) node->object) + indent;
  }

  return -1;
}

static char *
_parsetree_to_string( PARSE_TREE_NODE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_T * tree;
  char * str, * tmp, * indent_str;
  int bytes, i, len;

  bytes = _parsetree_to_string_bytes(node, indent, ctx);
  bytes += 1; /* null byte */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;

    if ( tree->nchildren == 0 )
    {
      snprintf(str, bytes, "(%s: )", ctx->morpheme_to_str(tree->nonterminal));
    }
    else
    {
      indent_str = _get_indent_str(indent);
      snprintf(str, bytes, "(%s:\n", ctx->morpheme_to_str(tree->nonterminal));
      for ( i = 0; i < tree->nchildren; i++ )
      {
        if ( i != 0 )
        {
          strcat(str, ",\n");
        }

        len = strlen(str);
        tmp = _parsetree_to_string(&tree->children[i], indent + 2, ctx);
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
    return {{prefix}}token_to_string((TOKEN_T *) node->object);
  }

  return NULL;
}

static void
_free_parse_tree( PARSE_TREE_NODE_T * node )
{
  int i;
  TOKEN_T * token;
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
    token = (TOKEN_T *) node->object;
  }
}

static int
_ast_to_string_bytes( ABSTRACT_SYNTAX_TREE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * list_node;
  ABSTRACT_SYNTAX_TREE_T * child;
  char * attr;
  int i, bytes;
  int initial_indent = (indent < 0) ? 0 : indent;
  indent = (indent < 0) ? -indent : indent;

  if ( node == NULL ) return 4; /* "none" */

  if ( node->type == AST_NODE_TYPE_OBJECT )
  {
    ast_object = (AST_OBJECT_T *) node->object;

    /*  <initial_indent, '(', ast_object->name, ':', '\n', indent>  */
    bytes = (initial_indent + indent + strlen(ast_object->name) + 3);

    for ( i = 0; i < ast_object->nchildren; i++ )
    {
      if ( i != 0 )
        /* <',', '\n', indent> as the separator */
        bytes += (2 + indent);

      attr = ast_object->children[i].name;
      child = ast_object->children[i].tree;

      /* <' ', ' ', attr, '=', _ast_to_string_bytes(child)> */
      bytes += (2 + 1 + strlen(attr) + _ast_to_string_bytes(child, -(indent + 2), ctx));
    }

    /*  <'\n', indent, ')'>  */
    bytes += (2 + indent);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_LIST )
  {
    ast_list = (AST_LIST_T *) node->object;

    if ( ast_list == NULL || ast_list->tree == NULL )
    {
      return indent + 2; /* "[]" */
    }

    /* <initial_indent, '[', '\n', indent> */
    bytes = (initial_indent + 2 + indent);

    for ( i = 0, list_node = ast_list; list_node && list_node->tree; i++, list_node = list_node->next )
    {
      if ( i != 0 )
        /* <',', '\n', indent> as the separator */
        bytes += (2 + indent);

      /* <' ', ' ', _ast_to_string_bytes(list_node->tree)> */
      bytes += 2 + _ast_to_string_bytes(list_node->tree, -(indent + 2), ctx);
    }

    /* <'\n', indent, ']'> */
    bytes += (indent + 2);
    return bytes;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    return initial_indent + token_to_string_bytes((TOKEN_T *) node->object) + indent;
  }

  return 4; /* "None" */
}

static char *
_ast_to_string( ABSTRACT_SYNTAX_TREE_T * node, int indent, PARSER_CONTEXT_T * ctx )
{
  AST_LIST_T * ast_list, * lnode;
  AST_OBJECT_T * ast_object;
  char * str, * key, * value, * indent_str, * tmp;
  int bytes, i;
  indent = (indent < 0) ? -indent : indent;

  bytes = _ast_to_string_bytes(node, indent, ctx) + 1;
  str = calloc( bytes, sizeof(char) );

  if ( node == NULL )
  {
    strcpy(str, "None");
    return str;
  }

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
      value = _ast_to_string(ast_object->children[i].tree, indent + 2, ctx);

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
      indent_str = _get_indent_str(indent);
      sprintf(str, "%s[]", indent_str);
      free(indent_str);
      return str;
    }

    indent_str = _get_indent_str(indent);
    snprintf(str, bytes, "%s[\n", indent_str);
    for ( i = 0, lnode = ast_list; lnode && lnode->tree; i++, lnode = lnode->next )
    {
      value = _ast_to_string(lnode->tree, indent + 2, ctx);
      snprintf(str + strlen(str), bytes - strlen(str), "%s", value);
      if ( lnode->next != NULL )
        strcat(str, ",\n");
      free(value);
    }
    snprintf(str + strlen(str), bytes - strlen(str), "\n%s]", indent_str);
    free(indent_str);
    return str;
  }

  if ( node->type == AST_NODE_TYPE_TERMINAL )
  {
    char * token_str = {{prefix}}token_to_string((TOKEN_T *) node->object);
    indent_str = _get_indent_str(indent);
    if (indent_str != NULL) {
      token_str = realloc(token_str, strlen(token_str) + strlen(indent_str) + 1);
      _prepend(token_str, indent_str);
      free(indent_str);
    }
    return token_str;
  }

  strcpy(str, "None");
  return str;
}

char *
{{prefix}}token_to_string(TOKEN_T * token)
{
  int bytes;
  char * str;

  bytes = token_to_string_bytes(token);
  bytes += 1; /* null byte */

  if ( bytes == -1 )
    return NULL;

  str = calloc( bytes, sizeof(char) );

  sprintf(
      str,
      "<%s (line %d col %d) `%s`>",
      {{prefix}}morpheme_to_str(token->terminal->id), token->lineno, token->colno, token->source_string
  );

  return str;
}

char *
{{prefix}}ast_to_string( ABSTRACT_SYNTAX_TREE_T * tree, PARSER_CONTEXT_T * ctx )
{
  return _ast_to_string(tree, 0, ctx);
}

char *
{{prefix}}parsetree_to_string( PARSE_TREE_T * tree, PARSER_CONTEXT_T * ctx )
{
  PARSE_TREE_NODE_T node;
  char * str;

  if ( tree == NULL )
  {
    str = calloc(3, sizeof(char));
    strcpy(str, "()");
    return str;
  }

  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  str = _parsetree_to_string(&node, 0, ctx);
  return str;
}

ABSTRACT_SYNTAX_TREE_T *
{{prefix}}parsetree_node_to_ast( PARSE_TREE_NODE_T * node )
{
  ABSTRACT_SYNTAX_TREE_T * ast = NULL;
  PARSE_TREE_T * tree;

  if ( node == NULL ) return NULL;

  if ( node->type == PARSE_TREE_NODE_TYPE_TERMINAL )
  {
    ast = calloc(1, sizeof(ABSTRACT_SYNTAX_TREE_T));
    ast->type = AST_NODE_TYPE_TERMINAL;
    ast->object = (AST_NODE_U *) node->object;
  }

  if ( node->type == PARSE_TREE_NODE_TYPE_PARSETREE )
  {
    tree = (PARSE_TREE_T *) node->object;
    if ( tree == NULL ) return NULL;
    if ( tree->list && strlen(tree->list) )
    {
      ast = __parsetree_node_to_ast_list(node);
    }
    else if ( tree->isExpr )
    {
      ast = __parsetree_node_to_ast_expr(node);
    }
    else
    {
      ast = __parsetree_node_to_ast_normal(node);
    }
  }

  return ast;
}

void
{{prefix}}free_parse_tree( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;

  if ( tree == NULL )
    return;

  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  _free_parse_tree(&node);
}

void
{{prefix}}free_ast( ABSTRACT_SYNTAX_TREE_T * ast )
{
  AST_OBJECT_T * ast_object;
  AST_LIST_T * ast_list, * current, * tmp;
  int i;

  if ( ast )
  {
    if ( ast->type == AST_NODE_TYPE_OBJECT )
    {
      ast_object = (AST_OBJECT_T *) ast->object;
      free(ast_object->name);

      for ( i = 0; i < ast_object->nchildren; i++ )
      {
        {{prefix}}free_ast(ast_object->children[i].tree);
      }

      free(ast_object->children);
      free(ast_object);
    }

    if ( ast->type == AST_NODE_TYPE_LIST )
    {
      ast_list = (AST_LIST_T *) ast->object;

      for ( current = ast_list; current != NULL; current = current->next )
      {
        if ( current->tree != NULL )
          {{prefix}}free_ast(current->tree);
      }

      current = ast_list;
      while ( current )
      {
        tmp = current;
        current = current->next;
        if ( tmp != NULL )
          free(tmp);
      }
    }

    if (ast->type == AST_NODE_TYPE_TERMINAL )
    {
      /* this data structure provided by the user */
    }

    free(ast);
  }
}

/* Section: Parser */

{% for nonterminal in grammar.ll1_nonterminals %}
static PARSE_TREE_T * parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
{% endfor %}

{% for expression_nonterminal in grammar.expression_nonterminals %}
static PARSE_TREE_T * parse_{{expression_nonterminal.string.lower()}}(PARSER_CONTEXT_T *);
static PARSE_TREE_T * _parse_{{expression_nonterminal.string.lower()}}(int, PARSER_CONTEXT_T *);
{% endfor %}

static void syntax_error( PARSER_CONTEXT_T * ctx, char * message );

/* index with {{prefix.upper()}}TERMINAL_E or {{prefix.upper()}}NONTERMINAL_E */
static char * {{prefix}}morphemes[] = {
{% for terminal in sorted(grammar.standard_terminals, key=lambda x: x.id) %}
  "{{terminal.string}}", /* {{terminal.id}} */
{% endfor %}

{% for nonterminal in sorted(grammar.nonterminals, key=lambda x: x.id) %}
  "{{nonterminal.string}}", /* {{nonterminal.id}} */
{% endfor %}
};

static int {{prefix}}first[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.first(nonterminal)])}}{{', ' if len(grammar.first(nonterminal)) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}follow[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)+2}}] = {
{% for nonterminal in sorted(grammar.nonterminals, key=lambda n: n.id) %}
  { {{', '.join([str(x.id) for x in grammar.follow(nonterminal)])}}{{', ' if len(grammar.follow(nonterminal)) else ''}}-2 },
{% endfor %}
};

static int {{prefix}}table[{{len(grammar.nonterminals)}}][{{len(grammar.standard_terminals)}}] = {
  {% py parse_table = grammar.parse_table %}
  {% for i in range(len(grammar.nonterminals)) %}
  { {{', '.join([str(rule.id) if rule else str(-1) for rule in parse_table[i]])}} },
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}nud_ast_types[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule, ExprRule) and isinstance(rule.nudAst, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

/* Index with rule ID */
static PARSETREE_TO_AST_CONVERSION_TYPE_E {{prefix}}ast_types[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
  AST_CREATE_OBJECT, /* ({{rule.id}}) {{rule}} */
    {% else %}
  AST_RETURN_INDEX, /* ({{rule.id}}) {{rule}} */
    {% endif %}
  {% endfor %}
};

static AST_CREATE_OBJECT_INIT {{prefix}}nud_ast_objects[] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule, ExprRule) and rule.nudAst and isinstance(rule.nudAst, AstSpecification) %}
      {% for i, key in enumerate(rule.nudAst.parameters.keys()) %}
  { {{rule.id}}, "{{rule.nudAst.name}}", "{{key}}", {{rule.nudAst.parameters[key] if rule.nudAst.parameters[key] != '$' else "'$'"}} },
      {% endfor %}

      {% if not len(rule.nudAst.parameters) %}
  { {{rule.id}}, "{{rule.nudAst.name}}", "", 0},
      {% endif %}
    {% endif %}
  {% endfor %}
  {0}
};

static AST_CREATE_OBJECT_INIT {{prefix}}ast_objects[] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
    {% if isinstance(rule.ast, AstSpecification) %}
      {% for i, key in enumerate(rule.ast.parameters.keys()) %}
  { {{rule.id}}, "{{rule.ast.name}}", "{{key}}", {{rule.ast.parameters[key] if rule.ast.parameters[key] != '$' else "'$'"}} },
      {% endfor %}

      {% if not len(rule.ast.parameters) %}
  { {{rule.id}}, "{{rule.ast.name}}", "", 0},
      {% endif %}
    {% endif %}
  {% endfor %}
  {0}
};

static int {{prefix}}ast_index[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
  {{rule.ast.idx if isinstance(rule.ast, AstTranslation) else 0}}, /* ({{rule.id}}) {{rule}} */
  {% endfor %}
};

static int {{prefix}}nud_ast_index[{{len(grammar.get_expanded_rules())}}] = {
  {% for rule in sorted(grammar.get_expanded_rules(), key=lambda x: x.id) %}
  {{rule.nudAst.idx if isinstance(rule, ExprRule) and isinstance(rule.nudAst, AstTranslation) else 0}}, /* ({{rule.id}}) {{rule}} */
  {% endfor %}
};

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

static int
advance(PARSER_CONTEXT_T * ctx)
{
  TOKEN_LIST_T * token_list = ctx->tokens;
  if ( token_list->current_index == token_list->ntokens ) {
    token_list->current = {{prefix.upper()}}TERMINAL_END_OF_STREAM;
    return token_list->current;
  }
  token_list->current_index += 1;
  token_list->current = token_list->tokens[token_list->current_index]->terminal->id;
  return token_list->current;
}

static TOKEN_T *
expect(int terminal_id, PARSER_CONTEXT_T * ctx)
{
  int current, next;
  TOKEN_T * current_token;
  TOKEN_LIST_T * token_list = ctx->tokens;
  char * message, * fmt;

  if ( token_list == NULL || token_list->current == {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    fmt = "No more tokens.  Expecting %s";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(terminal_id)) + 1, sizeof(char) );
    sprintf(message, fmt, {{prefix}}morpheme_to_str(terminal_id));
    syntax_error(ctx, message);
  }

  current = token_list->tokens[token_list->current_index]->terminal->id;
  current_token = token_list->tokens[token_list->current_index];

  if ( current != terminal_id )
  {
    char * token_string = (current != {{prefix.upper()}}TERMINAL_END_OF_STREAM) ?  {{prefix}}token_to_string(current_token) : strdup("(end of stream)");
    fmt = "Unexpected symbol (line %d, col %d) when parsing %s.  Expected %s, got %s.";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(terminal_id)) + strlen(token_string) + strlen(ctx->current_function) + 20, sizeof(char) );
    sprintf(message, fmt, current_token->lineno, current_token->colno, ctx->current_function, {{prefix}}morpheme_to_str(terminal_id), token_string);
    free(token_string);
    syntax_error(ctx, message);
  }

  next = advance(ctx);

  if ( next != {{prefix.upper()}}TERMINAL_END_OF_STREAM && !{{prefix.upper()}}IS_TERMINAL(next) )
  {
    fmt = "Invalid symbol ID: %d (%s)";
    message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(next)) + 10, sizeof(char) );
    sprintf(message, fmt, next, {{prefix}}morpheme_to_str(next));
    syntax_error(ctx, message);
  }

  return current_token;
}

static PARSETREE_TO_AST_CONVERSION_T *
get_default_ast_converter()
{
  PARSETREE_TO_AST_CONVERSION_T * converter = NULL;
  AST_RETURN_INDEX_T * ast_return_index;

  converter = calloc(1, sizeof(PARSETREE_TO_AST_CONVERSION_T));
  ast_return_index = calloc(1, sizeof(AST_RETURN_INDEX_T));
  ast_return_index->index = 0;
  converter->type = AST_RETURN_INDEX;
  converter->object = (PARSE_TREE_TO_AST_CONVERSION_U *) ast_return_index;
  return converter;
}

static PARSETREE_TO_AST_CONVERSION_T *
_get_ast_converter(int rule_id, PARSETREE_TO_AST_CONVERSION_TYPE_E * ast_types, AST_CREATE_OBJECT_INIT * ast_objects, int * ast_index)
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

static PARSETREE_TO_AST_CONVERSION_T *
get_nud_ast_converter(int rule_id)
{
  return _get_ast_converter(rule_id, &{{prefix}}nud_ast_types[0], &{{prefix}}nud_ast_objects[0], &{{prefix}}nud_ast_index[0]);
}

static PARSETREE_TO_AST_CONVERSION_T *
get_ast_converter(int rule_id)
{
  return _get_ast_converter(rule_id, &{{prefix}}ast_types[0], &{{prefix}}ast_objects[0], &{{prefix}}nud_ast_index[0]);
}

{% for expression_nonterminal in grammar.expression_nonterminals %}
{% py name = expression_nonterminal.string.lower() %}

static int infixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in grammar.get_rules(expression_nonterminal) if rule.operator and rule.operator.associativity in ['left', 'right']} %}

  {% for i in range(len(grammar.terminals)) %}
  {{0 if i not in operators else operators[i]}},
  {% endfor %}
};

static int prefixBp_{{name}}[{{len(grammar.terminals)}}] = {
  {% py operators = {rule.operator.operator.id: rule.operator.binding_power for rule in grammar.get_rules(expression_nonterminal) if rule.operator and rule.operator.associativity in ['unary']} %}

  {% for i in range(len(grammar.terminals)) %}
  {{0 if i not in operators else operators[i]}},
  {% endfor %}
};

static int
getInfixBp_{{name}}(int id)
{
  return infixBp_{{name}}[id];
}

static int
getPrefixBp_{{name}}(int id)
{
  return prefixBp_{{name}}[id];
}

static PARSE_TREE_T *
nud_{{name}}(PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  int current = ctx->tokens->current;
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{expression_nonterminal.string.upper()}};

  current = list->current;

  if ( list == NULL )
  {
    tree->ast_converter = get_default_ast_converter();
    return tree;
  }

  {% for i, rule in enumerate(grammar.get_expanded_rules(expression_nonterminal)) %}
    {% py ruleFirstSet = grammar.first(rule.production) %}

    {% if len(ruleFirstSet) and not ruleFirstSet.issuperset(grammar.first(expression_nonterminal))%}
  if ( {{' || '.join(['current == %d' % (x.id) for x in ruleFirstSet])}} )
  {
    // {{rule}}
    tree->ast_converter = get_nud_ast_converter({{rule.id}});
    tree->nchildren = {{len(rule.nud_production)}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));
    tree->nudMorphemeCount = {{len(rule.nud_production)}};
    {% for index, morpheme in enumerate(rule.nud_production.morphemes) %}
      {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect({{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
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
      {% endif %}
    {% endfor %}
    return tree;
  }
  {% endif %}
  {% endfor %}

  tree->ast_converter = get_default_ast_converter();
  return tree;
}

static PARSE_TREE_T *
led_{{name}}(PARSE_TREE_T * left, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * tree;
  TOKEN_LIST_T * list;
  int current = ctx->tokens->current;
  int modifier = 0;

  list = ctx->tokens;

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{expression_nonterminal.string.upper()}};

  if ( list == NULL )
    return tree;

  current = list->current;

  {% for rule in grammar.get_expanded_rules(expression_nonterminal) %}
    {% py led = rule.ledProduction.morphemes %}
    {% if len(led) %}
  if ( current == {{led[0].id}} ) /* {{led[0]}} */
  {
    tree->ast_converter = get_ast_converter({{rule.id}});
    tree->nchildren = {{len(led) + 1}};
    tree->children = calloc(tree->nchildren, sizeof(PARSE_TREE_NODE_T));

    {% if len(rule.nud_production) == 1 and isinstance(rule.nud_production.morphemes[0], NonTerminal) %}
      {% py nt = rule.nud_production.morphemes[0] %}
      {% if nt == rule.nonterminal or (isinstance(nt.macro, OptionalMacro) and nt.macro.nonterminal == rule.nonterminal) %}
    tree->isExprNud = 1;
      {% endif %}
    {% endif %}

    tree->children[0].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[0].object = (PARSE_TREE_NODE_U *) left;

      {% py associativity = {rule.operator.operator.id: rule.operator.associativity for rule in grammar.get_rules(expression_nonterminal) if rule.operator} %}
      {% for index, morpheme in enumerate(led) %}
        {% if isinstance(morpheme, Terminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_TERMINAL;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) expect( {{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
        {% elif isinstance(morpheme, NonTerminal) and morpheme.string.upper() == rule.nonterminal.string.upper() %}
    modifier = {{1 if rule.operator.operator.id in associativity and associativity[rule.operator.operator.id] == 'right' else 0}};
          {% if isinstance(rule.operator, InfixOperator) %}
    tree->isInfix = 1;
          {% endif %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) _parse_{{rule.nonterminal.string.lower()}}( getInfixBp_{{name}}({{rule.operator.operator.id}}) - modifier, ctx );
        {% elif isinstance(morpheme, NonTerminal) %}
    tree->children[{{index + 1}}].type = PARSE_TREE_NODE_TYPE_PARSETREE;
    tree->children[{{index + 1}}].object = (PARSE_TREE_NODE_U *) parse_{{morpheme.string.lower()}}(ctx);
        {% endif %}
      {% endfor %}
  }
    {% endif %}
  {% endfor %}

  return tree;
}
{% endfor %}

{% for nonterminal in grammar.ll1_nonterminals %}

static PARSE_TREE_T *
parse_{{nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  int current;
  TOKEN_LIST_T * tokens = ctx->tokens;
  PARSE_TREE_T * tree;
  char * message, * fmt;
  int rule = -1;

  ctx->current_function = "parse_{{nonterminal.string.lower()}}";

  tree = calloc(1, sizeof(PARSE_TREE_T));
  tree->nonterminal = {{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}};

    {% if isinstance(nonterminal.macro, SeparatedListMacro) %}
  tree->list = "slist";
    {% elif isinstance(nonterminal.macro, MorphemeListMacro) %}
  tree->list = "nlist";
    {% elif isinstance(nonterminal.macro, TerminatedListMacro) %}
  tree->list = "tlist";
    {% elif isinstance(nonterminal.macro, MinimumListMacro) %}
  tree->list = "mlist";
    {% elif isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
  tree->list = "otlist";
    {% else %}
  tree->list = NULL;
    {% endif %}

  current = tokens->current;

  {% if not grammar.must_consume_tokens(nonterminal) %}
  if ( current != {{prefix.upper()}}TERMINAL_END_OF_STREAM &&
       in_array({{prefix}}follow[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) &&
       !in_array({{prefix}}first[{{prefix.upper()}}NONTERMINAL_{{nonterminal.string.upper()}} - {{len(grammar.standard_terminals)}}], current) )
  {
    return tree;
  }
  {% endif %}

  if ( current == {{prefix.upper()}}TERMINAL_END_OF_STREAM )
  {
    {% if not grammar.must_consume_tokens(nonterminal) %}
    return tree;
    {% else %}
    syntax_error(ctx, strdup("Error: unexpected end of file"));
    {% endif %}
  }

  rule = {{prefix}}table[{{nonterminal.id - len(grammar.standard_terminals)}}][current];

    {% for index0, rule in enumerate([rule for rule in grammar.get_expanded_rules(nonterminal) if not rule.is_empty]) %}
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
    tree->children[{{index}}].object = (PARSE_TREE_NODE_U *) expect( {{prefix.upper()}}TERMINAL_{{morpheme.string.upper()}}, ctx );
          {% if isinstance(nonterminal.macro, SeparatedListMacro) or isinstance(nonterminal.macro, OptionallyTerminatedListMacro) %}
            {% if nonterminal.macro.separator == morpheme %}
    tree->listSeparator = tree->children[{{index}}].object;
            {% endif %}
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

    {% if grammar.must_consume_tokens(nonterminal) %}
  fmt = "Error: Unexpected symbol (%s) when parsing %s";
  message = calloc( strlen(fmt) + strlen({{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index]->terminal->id)) + strlen("parse_{{nonterminal.string.lower()}}") + 1, sizeof(char) );
  sprintf(message, fmt, {{prefix}}morpheme_to_str(tokens->tokens[tokens->current_index]->terminal->id), "parse_{{nonterminal.string.lower()}}");
  syntax_error(ctx, message);
  return NULL;
    {% else %}
  return tree;
    {% endif %}
}
{% endfor %}

#define HAS_MORE_TOKENS(ctx) (ctx->tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM)

{% for expression_nonterminals in grammar.expression_nonterminals %}

#define {{expression_nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) (rbp < getInfixBp_{{expression_nonterminal.string.lower()}}(ctx->tokens->current))

static PARSE_TREE_T *
_parse_{{expression_nonterminal.string.lower()}}(int rbp, PARSER_CONTEXT_T * ctx)
{
  PARSE_TREE_T * left = NULL;
  left = nud_{{expression_nonterminal.string.lower()}}(ctx);

  if ( left != NULL )
  {
    left->isExpr = 1;
    left->isNud = 1;
  }

  while ( HAS_MORE_TOKENS(ctx) && {{expression_nonterminal.string.upper()}}_LEFT_BINDING_POWER_LARGER(ctx, rbp) )
  {
    left = led_{{expression_nonterminal.string.lower()}}(left, ctx);
  }

  if ( left != NULL )
  {
    left->isExpr = 1;
  }

  return left;
}

static PARSE_TREE_T *
parse_{{expression_nonterminal.string.lower()}}(PARSER_CONTEXT_T * ctx)
{
  ctx->current_function = "parse_{{expression_nonterminal.string.lower()}}";
  return _parse_{{expression_nonterminal.string.lower()}}(0, ctx);
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
{{prefix}}parser_init( TOKEN_LIST_T * tokens )
{
  PARSER_CONTEXT_T * ctx;
  ctx = calloc(1, sizeof(PARSER_CONTEXT_T));
  ctx->tokens = tokens;
  ctx->morpheme_to_str = {{prefix}}morpheme_to_str;
  tokens->current_index = 0;
  tokens->current = tokens->tokens[0]->terminal->id;
  return ctx;
}

void
{{prefix}}parser_exit( PARSER_CONTEXT_T * ctx)
{
  SYNTAX_ERROR_T * error, * next;
  for ( error = ctx->syntax_errors; error != NULL; error = next )
  {
    next = error->next;
    free(error->message);
    free(error);
  }
  free(ctx);
}

void
syntax_error( PARSER_CONTEXT_T * ctx, char * message )
{
  SYNTAX_ERROR_T * syntax_error = calloc(1, sizeof(SYNTAX_ERROR_T));
  syntax_error->message = message;
  syntax_error->terminal = ctx->tokens->tokens[ctx->tokens->current_index]->terminal;
  syntax_error->next = NULL;

  if ( ctx->syntax_errors == NULL )
  {
    ctx->syntax_errors = syntax_error;
  }
  else
  {
    ctx->last->next = syntax_error;
  }

  ctx->last = syntax_error;
}

PARSE_TREE_T *
{{prefix}}parse(PARSER_CONTEXT_T * ctx, ENUM_{{prefix.upper()}}NONTERMINAL start)
{
  PARSE_TREE_T * tree;

  if ( start == -1 ) {
    start = {{prefix.upper()}}NONTERMINAL_{{grammar.start.string.upper()}};
  }

  tree = functions[start - {{len(grammar.standard_terminals)}}](ctx);

  if ( ctx->tokens->current != {{prefix.upper()}}TERMINAL_END_OF_STREAM ) {
    syntax_error(ctx, strdup("Finished parsing without consuming all tokens."));
  }

  return tree;
}

char *
{{prefix}}morpheme_to_str(int id)
{
  if ( id == -1 ) return "<end of stream>";
  return {{prefix}}morphemes[id];
}

int
{{prefix}}str_to_morpheme(const char * str)
{
  {% for terminal in grammar.standard_terminals %}
  if ( !strcmp(str, "{{terminal.string}}") )
    return {{terminal.id}};
  {% endfor %}

  {% for nonterminal in grammar.nonterminals %}
  if ( !strcmp(str, "{{nonterminal.string}}") )
    return {{nonterminal.id}};
  {% endfor %}

  return -1;
}

ABSTRACT_SYNTAX_TREE_T *
{{prefix}}ast( PARSE_TREE_T * tree )
{
  PARSE_TREE_NODE_T node;
  node.type = PARSE_TREE_NODE_TYPE_PARSETREE;
  node.object = (PARSE_TREE_NODE_U *) tree;
  return {{prefix}}parsetree_node_to_ast(&node);
}

/* Section: Main */

{% if add_main %}
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

static char * strdup2(const char *str) {
  int n = strlen(str) + 1;
  char *dup = malloc(n);
  if(dup) {
    strcpy(dup, str);
  }
  return dup;
}

#define strdup strdup2

TOKEN_LIST_T *
get_tokens(char * grammar, char * json_input, TOKEN_LIST_T * token_list) {
  TOKEN_T ** tokens;
  TOKEN_T * end_of_stream;
  int i, j, ntokens;
  json_value * json;
  TOKEN_FIELD_E field, field_mask;
  int (*terminal_str_to_id)(const char *);

  if ( strcmp("{{grammar.name}}", grammar) == 0 ) {
    terminal_str_to_id = {{grammar.name}}_str_to_morpheme;
  }

  end_of_stream = calloc(1, sizeof(TOKEN_T));
  end_of_stream->terminal = calloc(1, sizeof(TERMINAL_T));
  end_of_stream->terminal->id = -1;

  json = json_parse(json_input);

  if ( json == NULL ) {
    fprintf(stderr, "Invalid JSON input\n");
    exit(-1);
  }

  if ( json->type != json_array ) {
    fprintf(stderr, "get_tokens(): JSON input should be an array of tokens\n");
    exit(-1);
  }

  ntokens = json->u.array.length;
  tokens = calloc(ntokens + 1, sizeof(TOKEN_T *));
  tokens[ntokens] = end_of_stream;

  for ( i = 0; i < json->u.array.length; i++ ) {

    json_value * json_token = json->u.array.values[i];
    TOKEN_T * token;
    token = tokens[i] = calloc(1, sizeof(TOKEN_T));
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
  token_list->current = tokens[0]->terminal->id;
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
  int i, rval, rc;
  char * file_contents, * b64;
  int file_length;
  size_t b64_size = 2;
  FILE * fp;

  b64 = malloc(b64_size);

  char err[512];
  TOKEN_LIST_T * lexer_tokens;

  if (argc != 3 || (strcmp(argv[1], "parsetree") != 0 && strcmp(argv[1], "ast") != 0 {% if lexer %} && strcmp(argv[1], "tokens") != 0{% endif %})) {
    fprintf(stderr, "Usage: %s <parsetree|ast> <tokens_file>\n", argv[0]);
    {% if lexer %}
    fprintf(stderr, "Usage: %s <tokens> <source_file>\n", argv[0]);
    {% endif %}
    return -1;
  }

  fp = fopen(argv[2], "r");
  file_length = read_file(&file_contents, fp);

  {% if lexer %}
  if (!strcmp(argv[1], "tokens")) {
    {{prefix}}lexer_init();
    if ( {{prefix}}lexer_has_errors() ) {
        {{prefix}}lexer_print_errors();
    }
    lexer_tokens = {{prefix}}lex(file_contents, argv[2], &err[0]);
    if (lexer_tokens == NULL) {
        printf("%s\n", err);
        exit(1);
    }

    if (lexer_tokens->tokens[0]->terminal->id == {{prefix.upper()}}TERMINAL_END_OF_STREAM) {
        printf("[]\n");
        exit(0);
    }

    printf("[\n");
    for (i = 0; lexer_tokens->tokens[i]->terminal->id != {{prefix.upper()}}TERMINAL_END_OF_STREAM; i++) {
        while(1) {
            rc = base64_encode(
                (const char *) lexer_tokens->tokens[i]->source_string,
                strlen(lexer_tokens->tokens[i]->source_string),
                b64, b64_size
            );
            if (rc == 0) break;
            else if (rc == BASE64_OUTPUT_TOO_SMALL) {
                b64_size *= 2;
                b64 = realloc(b64, b64_size);
                continue;
            }
            else {
                printf("Error\n");
                exit(-1);
            }
        }

        printf(
          "    %c\"terminal\": \"%s\", \"resource\": \"%s\", \"line\": %d, \"col\": %d, \"source_string\": \"%s\"%c%s\n",
          '{',
          lexer_tokens->tokens[i]->terminal->string,
          lexer_tokens->tokens[i]->resource,
          lexer_tokens->tokens[i]->lineno,
          lexer_tokens->tokens[i]->colno,
          b64,
          '}',
          lexer_tokens->tokens[i+1]->terminal->id == {{prefix.upper()}}TERMINAL_END_OF_STREAM ? "" : ","
        );
    }
    printf("]\n");
    {{prefix}}lexer_destroy();
    return 0;
  }
  {% endif %}

  get_tokens("{{grammar.name}}", file_contents, &token_list);
  ctx = {{prefix}}parser_init(&token_list);
  parse_tree = {{prefix}}parse(ctx, -1);
  abstract_syntax_tree = {{grammar.name}}_ast(parse_tree);

  if ( ctx->syntax_errors ) {
    rval = 1;
    printf("%s\n", ctx->syntax_errors->message);
    goto exit;
    /*for ( error = ctx->syntax_errors; error; error = error->next )
    {
      printf("%s\n", error->message);
    }*/
  }

  if ( argc >= 3 && !strcmp(argv[1], "ast") ) {
    str = {{prefix}}ast_to_string(abstract_syntax_tree, ctx);
  } else {
    str = {{prefix}}parsetree_to_string(parse_tree, ctx);
  }

  rval = 0;
  printf("%s", str);

  {{grammar.name}}_parser_exit(ctx);
  {{prefix}}free_parse_tree(parse_tree);
  {{prefix}}free_ast(abstract_syntax_tree);

exit:
  free(b64);
  return rval;
}
{% endif %}

/* Section: Lexer */

{% if lexer %}
{% import re %}

/* index with {{prefix.upper()}}TERMINAL_E */
/*
static char * {{prefix}}morphemes[] = {
{% for terminal in sorted(lexer.terminals, key=lambda x: x.id) %}
    "{{terminal.string}}", * {{terminal.id}} *
{% endfor %}
};
*/

{{prefix.upper()}}LEXER_MODE_E {{prefix}}lexer_mode_enum(const char * mode) {
{% for mode, regex_list in lexer.items() %}
    if (strcmp(mode, "{{mode}}") == 0) {
        return {{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E;
    }
{% endfor %}
    return {{prefix.upper()}}LEXER_INVALID_MODE_E;
}

char * {{prefix}}lexer_mode_string({{prefix.upper()}}LEXER_MODE_E mode) {
{% for mode, regex_list in lexer.items() %}
    if ({{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E == mode) {
        return "{{mode}}";
    }
{% endfor %}
    return NULL;
}

static LEXER_REGEX_T *** lexer = NULL;

static TOKEN_T *
emit(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col)
{
    TOKEN_T * token;
    if (ctx->token_list->current_index + 2 == ctx->token_list->ntokens) {
        ctx->token_list->ntokens += 100;
        ctx->token_list->tokens = realloc(ctx->token_list->tokens, ctx->token_list->ntokens * sizeof(TOKEN_T *));
    }
    token = ctx->token_list->tokens[ctx->token_list->current_index++] = calloc(1, sizeof(TOKEN_T));
    token->lineno = line;
    token->colno = col;
    token->source_string = strdup(source_string);
    token->resource = strdup(ctx->resource);
    token->terminal = calloc(1, sizeof(TERMINAL_T));
    memcpy(token->terminal, terminal, sizeof(TERMINAL_T));
    return token;
}

{% if re.search(r'void\s*\*\s*default_action', lexer.code) is None %}
static void
default_action(LEXER_CONTEXT_T * ctx, TERMINAL_T * terminal, char * source_string, int line, int col)
{
    emit(ctx, terminal, source_string, line, col);
}
{% endif %}

/* START USER CODE */
{{lexer.code}}
/* END USER CODE */

{% if re.search(r'void\s*\*\s*init', lexer.code) is None %}
static void *
init() {
    return NULL;
}
{% endif %}

{% if re.search(r'void\s*destroy', lexer.code) is None %}
static void
destroy(void * context) {
    return;
}
{% endif %}

void
{{prefix}}lexer_init()
{
    LEXER_REGEX_T * r;
    LEXER_REGEX_OUTPUT_T * o;
    if (lexer != NULL) {
        return;
    }
    lexer = calloc({{len(lexer.keys())}} + 1, sizeof(LEXER_REGEX_T **));
{% for mode, regex_list in lexer.items() %}
    lexer[{{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E] = calloc({{len(regex_list)}} + 1, sizeof(LEXER_REGEX_T *));
  {% for i, regex in enumerate(regex_list) %}
    r = calloc(1, sizeof(LEXER_REGEX_T));
    r->regex = pcre_compile({{regex.regex}}, PCRE_UTF8, &r->pcre_errptr, &r->pcre_erroffset, NULL);
    r->pattern = {{regex.regex}};
    {% if len(regex.outputs) %}
    r->outputs = calloc({{len(regex.outputs)}}, sizeof(LEXER_REGEX_OUTPUT_T));

      {% for j, output in enumerate(regex.outputs) %}
    o = &r->outputs[{{j}}];
        {% if isinstance(output, RegexOutput) %}
    o->group = {{output.group if output.group is not None else -1}};
          {% if output.terminal %}
    o->terminal = calloc(1, sizeof(TERMINAL_T));
    o->terminal->string = "{{output.terminal.string.lower()}}";
    o->terminal->id = {{output.terminal.id}};
          {% else %}
    o->terminal = NULL;
          {% endif %}
    o->match_func = {{output.function if output.function else 'default_action'}};
        {% elif isinstance(output, LexerStackPush) %}
    o->stack_push = "{{output.mode}}";
        {% elif isinstance(output, LexerAction) %}
    o->action = "{{output.action}}";
        {% endif %}
      {% endfor %}

    {% else %}
    r->outputs = NULL;
    {% endif %}
    r->outputs_count = {{len(regex.outputs)}};
    lexer[{{prefix.upper()}}LEXER_{{mode.upper()}}_MODE_E][{{i}}] = r;
  {% endfor %}
{% endfor %}
}

int
{{prefix}}lexer_has_errors()
{
    int i, j;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            if (lexer[i][j]->regex == NULL) {
                return 1;
            }
        }
    }
    return 0;
}

void
{{prefix}}lexer_print_errors()
{
    int i, j, k;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            if (lexer[i][j]->regex == NULL) {
                char * prefix = "Error compiling regex: ";
                printf("%s%s\n", prefix, lexer[i][j]->pattern);
                for (k = 0; k < strlen(prefix) + lexer[i][j]->pcre_erroffset - 1; k++) {
                    printf(" ");
                }
                printf("^\n");
                printf("%s\n\n", lexer[i][j]->pcre_errptr);
            }
        }
    }
}

void
{{prefix}}lexer_destroy() {
    int i, j, k;
    for (i = 0; lexer[i]; i++) {
        for (j = 0; lexer[i][j]; j++) {
            pcre_free(lexer[i][j]->regex);
            for (k = 0; k < lexer[i][j]->outputs_count; k++) {
                free(lexer[i][j]->outputs[k].terminal);
            }
            free(lexer[i][j]->outputs);
            free(lexer[i][j]);
        }
    }
    free(lexer);
    lexer = NULL;
}

static char *
get_line(char * s, int line)
{
    char * p, * start, * rval;
    int current_line = 1, length = 0;
    if ( line < 1 ) {
        return NULL;
    }
    for( p = start = s; *p; p++ ) {
        if (*p == '\n') {
            if ( line == current_line ) {
                break;
            }
            current_line++;
            length = 0;
            start = p + 1;
        } else {
            length++;
        }
    }
    if (current_line < line) {
        return NULL;
    }
    rval = calloc(length + 1, sizeof(char));
    strncpy(rval, start, length);
    return rval;
}

static void
unrecognized_token(char * string, int line, int col, char * message) {
    char * bad_line = get_line(string, line);
    char * spaces = calloc(col+1, sizeof(char));
    memset(spaces, ' ', col-1);
    sprintf(message, "Unrecognized token on line %d, column %d:\n\n%s\n%s^",
        line, col, bad_line, spaces
    );
    free(spaces);
    free(bad_line);
}

static void
advance_line_col(char * string, int length, int * line, int * col) {
    int i;
    for (i = 0; i < length; i++) {
        if (string[i] == '\n') {
            *line += 1;
            *col = 1;
        } else {
            if ((string[i] & 0xc0) != 0x80) {
                *col += 1;
            }
        }
    }
}

static void
advance_string(LEXER_CONTEXT_T * ctx, int length) {
    advance_line_col(ctx->string, length, &ctx->line, &ctx->col);
    ctx->string += length;
}

static int
next(LEXER_CONTEXT_T * ctx) {
    int rc, i, j;
    int group_line, group_col;
    int ovector_count = 30, group_strlen, match_length;
    int ovector[ovector_count];
    char ** match_groups;
    {{prefix.upper()}}LEXER_MODE_E mode = ({{prefix.upper()}}LEXER_MODE_E) ctx->stack[ctx->stack_top];

    for (i = 0; lexer[mode][i]; i++) {
        rc = pcre_exec(lexer[mode][i]->regex, NULL, ctx->string, strlen(ctx->string), 0, PCRE_ANCHORED, ovector, ovector_count);
        if (rc >= 0) {
            match_length = ovector[1] - ovector[0];

            if (lexer[mode][i]->outputs_count == 0 || lexer[mode][i]->outputs == NULL) {
                advance_string(ctx, match_length);
                return TRUE;
            }

            match_groups = calloc(rc+1, sizeof(char *));
            for (j = 0; j < rc; j++) {
                char * substring_start = ctx->string + ovector[2*j];
                group_strlen = ovector[2*j+1] - ovector[2*j];
                match_groups[j] = calloc(group_strlen + 1, sizeof(char));
                strncpy(match_groups[j], substring_start, group_strlen);
            }

            for (j = 0; j < lexer[mode][i]->outputs_count; j++) {
                if (lexer[mode][i]->outputs[j].stack_push != NULL) {
                    if (ctx->stack_top + 1 == ctx->stack_size) {
                        ctx->stack_size *= 2;
                        ctx->stack = realloc(ctx->stack, ctx->stack_size);
                    }
                    ctx->stack[++ctx->stack_top] = {{prefix}}lexer_mode_enum(lexer[mode][i]->outputs[j].stack_push);
                } else if (lexer[mode][i]->outputs[j].action != NULL) {
                    if (ctx->stack_top == 0) {
                        printf("Error: stack empty, can't pop\n");
                        exit(-1);
                    }
                    ctx->stack_top--;
                } else {
                    lexer_match_function match_func = lexer[mode][i]->outputs[j].match_func;
                    group_line = ctx->line;
                    group_col = ctx->col;
                    if (lexer[mode][i]->outputs[j].group > 0) {
                        advance_line_col(ctx->string, ovector[2*lexer[mode][i]->outputs[j].group] - ovector[0], &group_line, &group_col);
                    }
                    match_func(
                        ctx,
                        lexer[mode][i]->outputs[j].terminal,
                        lexer[mode][i]->outputs[j].group >= 0 ? match_groups[lexer[mode][i]->outputs[j].group] : "",
                        group_line,
                        group_col
                    );
                }
            }

            for (j = 0; match_groups[j]; j++) {
                free(match_groups[j]);
            }
            free(match_groups);
            advance_string(ctx, match_length);
            return TRUE;
        }
    }
    return FALSE;
}

TOKEN_LIST_T *
{{prefix}}lex(char * string, char * resource, char * error) {
    char * string_current = string;
    TERMINAL_T end_of_stream;
    LEXER_CONTEXT_T * ctx = NULL;
    TOKEN_LIST_T * token_list;

    ctx = calloc(1, sizeof(LEXER_CONTEXT_T));
    ctx->string = string_current;
    ctx->resource = resource;
    ctx->token_list = calloc(1, sizeof(TOKEN_LIST_T));
    ctx->token_list->ntokens = 100;
    ctx->token_list->current_index = 0;
    ctx->token_list->tokens = calloc(ctx->token_list->ntokens, sizeof(TOKEN_LIST_T *));
    ctx->stack_size = 10;
    ctx->stack_top = 0;
    ctx->stack = calloc(ctx->stack_size, sizeof(int));
    ctx->stack[0] = {{prefix.upper()}}LEXER_DEFAULT_MODE_E;
    ctx->line = 1;
    ctx->col = 1;
    ctx->user_context = init();

    while (strlen(ctx->string)) {
        int matched = next(ctx);

        if (matched == FALSE) {
            unrecognized_token(string, ctx->line, ctx->col, error);
            free(ctx->token_list);
            free(ctx->stack);
            free(ctx);
            return NULL;
        }
    }

    end_of_stream.id = {{prefix.upper()}}TERMINAL_END_OF_STREAM;
    emit(ctx, &end_of_stream, "<end of stream>", ctx->line, ctx->col);

    token_list = ctx->token_list;
    token_list->ntokens = token_list->current_index - 1;
    token_list->current_index = 0;

    destroy(ctx->user_context);
    free(ctx->stack);
    free(ctx);
    return token_list;
}

void
{{prefix}}free_token_list(TOKEN_LIST_T * list) {
    if (list != NULL) {
        if (list->tokens != NULL) free(list->tokens);
        free(list);
    }
}
{% endif %}
