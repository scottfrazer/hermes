c:
	hermes generate --language=c simple.gr
	hermes generate --language=c test.gr
	gcc -g -o ctest -lpcre -std=c99 ctest.c *_parser.c
	./ctest
python:
	python python.py
java:
	hermes generate --language=java test.gr
	javac *.java
	java JavaTest
javascript:
	hermes generate --language=javascript --nodejs test.gr
	node javascript.js
clean:
	rm -rf *.dSYM ctest *_parser.c *_parser.h *.pyc *Parser.java *.class *_parser.js
