#!/bin/bash
set -e -x
hermes generate -d hermes/parser -l python grammar.zgr
sed -i.bak 's/from ParserCommon import/from hermes.parser.ParserCommon import/g' hermes/parser/grammar_Parser.py
rm hermes/parser/grammar_Parser.py.bak
