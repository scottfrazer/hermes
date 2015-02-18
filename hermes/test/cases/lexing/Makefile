all: c_lexer python_lexer java_lexer js_lexer
java_lexer: java_files java_compile
java_compile:
	javac -cp java java/*.java
	-java -cp java GrammarParser tokens source &> java/tokens
python_lexer: python_files
js_lexer: js_files
	-node js/main.js tokens source &> js/tokens
c_lexer: c_files
	gcc -o c/lexer c/*.c -g -Wall -pedantic -std=c99 -lpcre
	-c/lexer tokens source &> c/tokens
java_files: java_dir
	hermes generate --language=java --add-main --directory=java grammar.zgr
python_files: python_dir
	hermes generate --language=python --add-main --directory=python grammar.zgr
	-python python/grammar_parser.py tokens source &> python/tokens
c_files: c_dir
	hermes generate --language=c --add-main --directory=c grammar.zgr
js_files: js_dir
	hermes generate --language=javascript --add-main --nodejs --directory=js grammar.zgr
c_dir:
	-mkdir c
python_dir:
	-mkdir python
java_dir:
	-mkdir java
js_dir:
	-mkdir js
clean:
	-rm -rf java c python js
