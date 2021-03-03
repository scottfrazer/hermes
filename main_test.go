package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func TokenizeGrammar(file string) (*TokenStream, error) {
	bytes, err := ioutil.ReadFile(file)
	if err != nil {
		return nil, err
	}
	lexer := NewHermesLexer()
	handler := &DefaultSyntaxErrorHandler{nil}
	stream, err := lexer.Lex(string(bytes), "grammar.hgr", handler)
	if err != nil {
		return nil, err
	}
	return stream, nil
}

func ParseGrammar(file string) (*parseTree, error) {
	parser := NewHermesParser()
	tokens, err := TokenizeGrammar(file)
	handler := &DefaultSyntaxErrorHandler{nil}
	if err != nil {
		return nil, err
	}
	return parser.ParseTokens(tokens, handler)
}

func diff(f1, f2 string) (int, string, error) {
	var outbuf, errbuf bytes.Buffer
	cmd := exec.Command("git", "diff", "--no-index", "--color", f1, f2)
	cmd.Stdout = &outbuf
	cmd.Stderr = &errbuf

	if err := cmd.Start(); err != nil {
		return 0, "", err
	}

	rc := 0
	if err := cmd.Wait(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			rc = exit.Sys().(syscall.WaitStatus).ExitStatus()
		}
	}
	return rc, outbuf.String(), nil
}

func compare(t *testing.T, grammarPath string, operation func(string) []byte, expectedResultsPath string) {
	tmpfile, err := ioutil.TempFile("", "sapling")
	if err != nil {
		t.Errorf("error while creating temp file")
	}
	defer os.Remove(tmpfile.Name())

	actualResults := operation(grammarPath)

	if _, err := tmpfile.Write(actualResults); err != nil {
		t.Errorf("error writing temp file")
	}

	rc, stdout, err := diff(expectedResultsPath, tmpfile.Name())

	if err != nil {
		t.Errorf("error diffing")
	}

	if rc != 0 || len(stdout) != 0 {
		t.Errorf("differences were detected")
		fmt.Println(stdout)
	}

	if err := tmpfile.Close(); err != nil {
		t.Errorf("error closing temp file")
	}
}

func TestSaplingParser(t *testing.T) {
	root := "hermes/test/cases/grammar"
	testdirs, err := ioutil.ReadDir(root)
	if err != nil {
		t.Errorf("could not read dir")
	}

	for _, dir := range testdirs {
		testPath := filepath.Join(root, dir.Name())
		grammarPath := filepath.Join(testPath, "grammar.hgr")
		tokensPath := filepath.Join(testPath, "tokens")
		parseTreePath := filepath.Join(testPath, "parse_tree")
		astPath := filepath.Join(testPath, "ast")

		t.Run(tokensPath, func(t *testing.T) {
			generateTokens := func(path string) []byte {
				tokenStream, err := TokenizeGrammar(path)
				if err != nil {
					t.Errorf("error while tokenizing")
				}

				var tokenStrings []string
				for _, token := range tokenStream.tokens {
					tokenStrings = append(tokenStrings, token.String())
				}
				return []byte(strings.Join(tokenStrings, "\n"))
			}

			compare(t, grammarPath, generateTokens, tokensPath)
		})

		t.Run(parseTreePath, func(t *testing.T) {
			generateTree := func(path string) []byte {
				tree, err := ParseGrammar(grammarPath)
				if err != nil {
					t.Errorf("error while parsing")
				}
				return []byte(tree.PrettyString())
			}
			compare(t, grammarPath, generateTree, parseTreePath)
		})

		t.Run(astPath, func(t *testing.T) {
			generateAst := func(path string) []byte {
				tree, err := ParseGrammar(grammarPath)
				if err != nil {
					t.Errorf("error while tokenizing")
				}
				return []byte(tree.Ast().PrettyString())
			}
			compare(t, grammarPath, generateAst, astPath)
		})
	}
}
