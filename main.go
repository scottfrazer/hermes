package main

import (
	"fmt"
	"io/ioutil"
	"os"

	"github.com/alecthomas/kong"
)

type Context struct {
	Debug bool
}

type AnalyzeCmd struct {
	Grammar string `arg help:"Grammar file" type:"path"`
}

func (cmd *AnalyzeCmd) Run(ctx *Context) error {
	fmt.Println("analyze", cmd.Grammar)
	return nil
}

type GenerateCmd struct {
	Grammar string `arg help:"Grammar file" type:"path"`
}

func (cmd *GenerateCmd) Run(ctx *Context) error {
	fmt.Println("generate", cmd.Grammar)
	return nil
}

type TokenizeCmd struct {
	Grammar string `arg help:"Grammar file" type:"path"`
}

func (cmd *TokenizeCmd) Run(ctx *Context) error {
	bytes, err := ioutil.ReadFile(cmd.Grammar)
	if err != nil {
		fmt.Printf("Error reading file %s: %s", os.Args[2], err)
		os.Exit(-1)
	}
	lexer := NewHermesLexer()
	handler := &DefaultSyntaxErrorHandler{nil}
	tokens, err := lexer.Lex(string(bytes), os.Args[2], handler)
	if err != nil {
		return err
	}
	for _, token := range tokens.tokens {
		fmt.Printf("%s\n", token.String())
	}
	return nil
}

type ParseCmd struct {
	Grammar string `arg help:"Grammar file" type:"path"`
}

func (cmd *ParseCmd) Run(ctx *Context) error {
	bytes, err := ioutil.ReadFile(cmd.Grammar)
	if err != nil {
		fmt.Printf("Error reading file %s: %s", os.Args[2], err)
		os.Exit(-1)
	}
	parser := NewHermesParser()
	lexer := NewHermesLexer()
	handler := &DefaultSyntaxErrorHandler{nil}
	tokens, err := lexer.Lex(string(bytes), os.Args[2], handler)
	if err != nil {
		fmt.Printf("%s\n", err)
		os.Exit(-1)
	}
	tree, err := parser.ParseTokens(tokens, handler)
	if err != nil {
		fmt.Printf("%s\n", err)
		os.Exit(-1)
	}
	ast := tree.Ast()
	if ast != nil {
		fmt.Println(ast.PrettyString())
	}
	return nil
}

var cli struct {
	Debug    bool        `help:"Enable debug mode."`
	Analyze  AnalyzeCmd  `cmd help:"Analyze Grammar"`
	Generate GenerateCmd `cmd help:"Generate source code for grammar"`
	Tokenize TokenizeCmd `cmd help:"Tokenize input based on a grammar"`
	Parse    ParseCmd    `cmd help:"Parse input based on a grammar"`
}

func main() {
	ctx := kong.Parse(&cli)
	err := ctx.Run(&Context{Debug: cli.Debug})
	ctx.FatalIfErrorf(err)
}
