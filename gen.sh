#!/bin/bash
set -e -x
hermes generate -d hermes/parser -l python grammar.zgr
mv hermes/parser/grammar/Parser.py hermes/parser/grammar_Parser.py
mv hermes/parser/Common.py hermes/parser/ParserCommon.py
rm -rf hermes/parser/grammar
sed -i.bak 's/from ParserCommon import/from hermes.parser.ParserCommon import/g' hermes/parser/grammar_Parser.py
rm hermes/parser/grammar_Parser.py.bak
