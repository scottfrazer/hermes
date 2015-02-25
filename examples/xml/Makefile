c:
	hermes generate --language=c xml.hgr
	gcc -g -o test -lpcre -std=c99 test.c *_parser.c
	./test
python:
	python test.py
java:
	hermes generate --language=java xml.hgr
	javac *.java
	java test
javascript:
	hermes generate --language=javascript --nodejs xml.hgr
	node test.js
clean:
	rm -rf *.dSYM test *_parser.c *_parser.h *.pyc *Parser.java *.class *_parser.js
