all: c_parser python_parser
python_parser: Parser.py ParserCommon.py ParserMain.py
c_parser: grammar_parser.c grammar_parser.h parser_common.c parser_common.h parser_main.c
	gcc -o parser grammar_parser.c parser_common.c parser_main.c -g -Wall -pedantic -ansi -std=c99
Parser.py ParserCommon.py ParserMain.py:
	hermes generate --language=python --add-main grammar.zgr
grammar_parser.c grammar_parser.h parser_common.c parser_common.h parser_main.c:
	hermes generate --language=c --add-main grammar.zgr
clean:
	rm -rf *.c *.h __pycache__ parser hermes.log *.py parser.dSYM
