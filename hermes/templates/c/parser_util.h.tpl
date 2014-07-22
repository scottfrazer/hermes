#ifndef __PARSER_UTIL_H
#define __PARSER_UTIL_H

#include <stdio.h>
#include <ctype.h>

#define BASE64_OUTPUT_TOO_SMALL 1
#define BASE64_INPUT_EQUALS_OUTPUT 2
#define BASE64_INPUT_MALFORMED 3
#define BASE64_NULL_OUTPUT 4

#define READ_FILE_BUFFER_SIZE 256

int base64_encode(const char * input, size_t input_length, char * output, size_t output_length);
int base64_decode(const char * input, char * output, size_t output_length, size_t * decoded_length);

int read_file(char ** content, FILE * fp);

/* JSON parsing */

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

json_value * json_parse(const json_char * json);
json_value * json_parse_ex (json_settings * settings, const json_char * json, char * error);

void json_value_free (json_value *);

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

/* JSON parsing */

#endif
