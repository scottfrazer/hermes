TOKENS=`python -c "print(','.join(filter(lambda x:x, open('tokens').read().split('\n'))))"`

all: Parser.py cparser

Parser.py:
	hermes generate grammar.zgr --language=python --add-main --tokens=$(TOKENS)

parser.c parser.h:
	hermes generate grammar.zgr --language=c --add-main --tokens=$(TOKENS)

cparser: parser.c parser.h
	gcc -o parser parser.c -Wall -std=c99 -pedantic -g

clean:
	rm -rf Parser.py parser.c parser.h parser.dSYM hermes.log parser
