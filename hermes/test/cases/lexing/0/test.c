#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static char * get_line(char * s, int line) {
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

static void unrecognized_token(char * string, int line, int col, char * message) {
    char * bad_line = get_line(string, line);
    char * spaces = calloc(col+1, sizeof(char));
    memset(spaces, ' ', col-1);
    sprintf(message, "Unrecognized token on line %d, column %d:\n\n%s\n%s^",
        line, col, bad_line, spaces
    );
    free(spaces);
    free(bad_line);
}

int main() {
    char * l;
    char message[512];
    unrecognized_token("\n\n\naaaa aaaa\n\nbbb bbb bbb\nc c cc c c\nd", 6, 3, &message[0]);
    printf("%s\n", message);
}
