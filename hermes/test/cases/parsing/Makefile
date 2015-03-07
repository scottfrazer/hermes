SHELL = /bin/bash
all: c python java js
java:
	-mkdir java
	hermes generate --language=java --add-main --directory=java grammar.zgr
	javac -cp java java/*.java
	-java -cp java GrammarParser parsetree tokens &>java/parsetree
	-java -cp java GrammarParser ast tokens &>java/ast
python:
	-mkdir python
	hermes generate --language=python --add-main --directory=python grammar.zgr
	-python python/grammar_parser.py parsetree tokens &> python/parsetree
	-python python/grammar_parser.py ast tokens &> python/ast
js:
	-mkdir js
	hermes generate --language=javascript --add-main --nodejs --directory=js grammar.zgr
	-node js/grammar_parser.js parsetree tokens &>js/parsetree
	-node js/grammar_parser.js ast tokens &>js/ast
c:
	-mkdir c
	hermes generate --language=c --add-main --directory=c grammar.zgr
	gcc -o c/parser c/*.c -g -std=c99
	-c/parser parsetree tokens &>c/parsetree
	-c/parser ast tokens &>c/ast
clean:
	-rm -rf java c python js
