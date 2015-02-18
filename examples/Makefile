c:
	hermes generate --language=c simple.gr
	hermes generate --language=c test.gr
	gcc -g -o ctest -lpcre -std=c99 ctest.c *_parser.c
	./ctest
python:
	python python.py
java:
	hermes generate --language=java test.gr --add-main
	javac TestParser.java
	java TestParser
clean:
	rm -rf *.dSYM ctest *_parser.c *_parser.h *.pyc *Parser.java *.class
