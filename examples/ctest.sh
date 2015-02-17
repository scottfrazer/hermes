set -x
hermes generate --language=c simple.gr
hermes generate --language=c test.gr
gcc -g -o ctest -lpcre -std=c99 ctest.c *_parser.c
