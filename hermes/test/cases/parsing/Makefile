all: c_parser python_parser java_parser
java_parser: java_files
	javac -cp java java/*.java
	-java -cp java ParserMain parsetree tokens &>java/parsetree
	-java -cp java ParserMain ast tokens &>java/ast
python_parser: python_files
c_parser: c_files
	gcc -o c/parser c/*.c -g -std=c99
	-c/parser parsetree tokens &>c/parsetree
	-c/parser ast tokens &>c/ast
java_files: java_dir
	hermes generate --language=java --add-main --directory=java grammar.zgr
	cp -r ../javacp/org java/
python_files: python_dir
	hermes generate --language=python --add-main --directory=python grammar.zgr
	-python -m python.grammar.Parser --file=tokens --out=parsetree &> python/parsetree
	-python -m python.grammar.Parser --file=tokens --out=ast &> python/ast
c_files: c_dir
	hermes generate --language=c --add-main --directory=c grammar.zgr
c_dir:
	-mkdir c
python_dir:
	-mkdir python
java_dir:
	-mkdir java
clean:
	-rm -rf java c python
