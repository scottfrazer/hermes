all: c python java js go
java:
	-mkdir java
	hermes generate --language=java --add-main --directory=java grammar.hgr
	javac -cp java java/*.java
	-java -cp java GrammarParser tokens source &> java/tokens
	-java -cp java GrammarParser parsetree source &> java/parsetree
	-java -cp java GrammarParser ast source &> java/ast
python:
	-mkdir python
	hermes generate --language=python --add-main --directory=python grammar.hgr
	-python python/grammar_parser.py tokens source &> python/tokens
	-python python/grammar_parser.py parsetree source &> python/parsetree
	-python python/grammar_parser.py ast source &> python/ast
js:
	-mkdir js
	hermes generate --language=javascript --add-main --nodejs --directory=js grammar.hgr
	-node js/grammar_parser.js tokens source &> js/tokens
	-node js/grammar_parser.js parsetree source &> js/parsetree
	-node js/grammar_parser.js ast source &> js/ast
c:
	-mkdir c
	hermes generate --language=c --add-main --directory=c grammar.hgr
	gcc -o c/parser c/*.c -g -Wall -pedantic -std=c99 -lpcre
	-c/parser tokens source &> c/tokens
	-c/parser parsetree source &> c/parsetree
	-c/parser ast source &> c/ast
go:
	-mkdir go
	hermes generate --language=go --add-main --directory=go grammar.hgr
	go build go/grammar_parser.go
	-go/parser tokens source &> c/tokens
	-go/parser parsetree source &> c/parsetree
	-go/parser ast source &> c/ast
clean:
	-rm -rf java c python js go
