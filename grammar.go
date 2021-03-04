package main

import (
	"fmt"
	"io"
)

type Grammar struct {
	Lexer  *Lexer
	Parser *Parser
}

type Lexer struct {
}

func NewLexer(ast *Ast) *Lexer {
	return nil
}

type Parser struct {
}

func AstOrError(n AstNode) (*Ast, error) {
	switch node := n.(type) {
	case *Ast:
		return node, nil
	default:
		return nil, fmt.Errorf("unexpected node: ")
	}
}

// func AstListOrError(n AstNode) ([]AstNode, error) {
// 	switch node := n.(type) {
// 	case *AstList:
// 		return *node.(*AstList), nil
// 	default:
// 		return nil, fmt.Errorf("unexpected node: ")
// 	}
// }

func LoadGrammarFromSource(reader io.Reader, resource string) (*Grammar, error) {
	contents, err := io.ReadAll(reader)
	if err != nil {
		return nil, err
	}

	handler := &DefaultSyntaxErrorHandler{nil}
	tokens, err := NewHermesLexer().Lex(string(contents), resource, handler)

	if err != nil {
		return nil, err
	}

	tree, err := NewHermesParser().ParseTokens(tokens, handler)
	if err != nil {
		return nil, err
	}

	ast := tree.Ast()

	node, err := AstOrError(ast)
	if err != nil {
		return nil, err
	}

	var lexer *Lexer
	if val, ok := node.attributes["body"]; ok {
		for _, item := range *val.(*AstList) {
			item, err := AstOrError(item)
			if err != nil {
				return nil, err
			}
			if item.name == "Lexer" {
				lexer = NewLexer(item)
			}
			fmt.Printf("%s\n", item.PrettyString())
		}
	}
	_ = lexer

	return nil, nil
}
