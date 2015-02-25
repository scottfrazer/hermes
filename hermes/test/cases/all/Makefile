all: c python java js
java:
	-mkdir java
	hermes generate --language=java --add-main --directory=java grammar.zgr
	javac -cp java java/*.java
	-java -cp java GrammarParser tokens source &> java/tokens
	-java -cp java GrammarParser parsetree java/tokens &> java/parsetree
	-java -cp java GrammarParser ast java/tokens &> java/ast
python:
	-mkdir python
	hermes generate --language=python --add-main --directory=python grammar.zgr
	-python python/grammar_parser.py tokens source &> python/tokens
	-python python/grammar_parser.py parsetree python/tokens &> python/parsetree
	-python python/grammar_parser.py ast python/tokens &> python/ast
js:
	-mkdir js
	hermes generate --language=javascript --add-main --nodejs --directory=js grammar.zgr
	-node js/grammar_parser.js tokens source &> js/tokens
	-node js/grammar_parser.js parsetree js/tokens &> js/parsetree
	-node js/grammar_parser.js ast js/tokens &> js/ast
c:
	-mkdir c
	hermes generate --language=c --add-main --directory=c grammar.zgr
	gcc -o c/lexer c/*.c -g -Wall -pedantic -std=c99 -lpcre
	-c/lexer tokens source &> c/tokens
	-c/lexer parsetree c/tokens &> c/parsetree
	-c/lexer ast c/tokens &> c/ast
clean:
	-rm -rf java c python js
