import hermes

simple = """
grammar {
  lexer<python> {
    r'a' -> :a
    r'b' -> :b
    r'\s+' -> null
  }
  parser<ll1> {
    $start = :a $sub :b
    $sub = :a $sub :b | :_empty
  }
}
"""

with open('json.gr') as fp:
    json_parser = hermes.compile(fp, module='json_parser', debug=False)
tree = json_parser.parse('{"a": 1, "b": [1,2.3e4,-3E-4], "this is a key":[false, true, false]}')
print(tree.dumps(indent=2, color=json_parser.term_color))
print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))

simple_parser = hermes.compile(simple, module='simple_parser', debug=False)
tree = simple_parser.parse('aaabbb')
print(tree.dumps(indent=2, color=json_parser.term_color))
#print(tree.dumps(color=json_parser.term_color))
#print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))
