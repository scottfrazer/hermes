Migration Plan
--------------

Phase 1: bootstrap Golang parser

1) Update all tests to include a parse tree and AST for the grammar itself based on the current Python Hermes parser
2) Generate a Golang Hermes parser from the Python Hermes parser
    2a) need a way to parse `code<lang>` blocks
    2b) need a way to parse prefix/infix/mixfix rules
3) Create go tests that assert that all parse trees and ASTs from step (1) work with the Golang parser

After this step is completed, we now have a respectable Golang parser for Hermes grammar files.

Phase 2: implement Golang backend code

1) Create code to transform Hermes AST -> Golang source code via Golang templates.  Use this opportunity to clean up abstractions.

CLI
---
hermes analyze grammar.hgr

hermes generate-go grammar.hgr [-o dir] [--package=main]
hermes tokenize-go grammar.hgr < input.txt
hermes parse-go [--ast] grammar.hgr < input.txt

hermes generate-java grammar.hgr [-o dir] [--package=org.my.package]
hermes tokenize-java grammar.hgr < input.txt
hermes parse-java [--ast] grammar.hgr < input.txt
