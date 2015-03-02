all: c python java js
java:
	-mkdir java
	hermes generate --language=java --add-main --directory=java grammar.zgr
	javac -cp java java/*.java
	-java -cp java GrammarParser tokens source &> java/tokens
python:
	-mkdir python
	hermes generate --language=python --add-main --directory=python grammar.zgr
	-python python/grammar_parser.py tokens source &> python/tokens
js:
	-mkdir js
	hermes generate --language=javascript --add-main --nodejs --directory=js grammar.zgr
	-node js/grammar_parser.js tokens source &> js/tokens
c:
	-mkdir c
	hermes generate --language=c --add-main --directory=c grammar.zgr
	gcc -o c/lexer c/*.c -g -Wall -pedantic -std=c99 -lpcre
	-c/lexer tokens source &> c/tokens
clean:
	-rm -rf java c python js
