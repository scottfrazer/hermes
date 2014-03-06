all: c_parser python_parser java_parser
java_parser: java_files
	javac -cp java java/*.java
python_parser: python_files
c_parser: c_files
	gcc -o c/parser c/*.c -g -Wall -pedantic -ansi -std=c99
java_files: java_dir
	hermes generate --language=java --add-main --directory=java grammar.zgr
	cp -r ../javacp/org java/
python_files: python_dir
	hermes generate --language=python --add-main --directory=python grammar.zgr
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
