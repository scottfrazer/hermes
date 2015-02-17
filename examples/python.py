import hermes

grammar = """
grammar {
  lexer<python> {
    r'{' -> :lbrace
    r'}' -> :rbrace
    r'"([^"]+)"' -> :string
    r'\[' -> :lsquare
    r'\]' -> :rsquare
    r'[0-9]+' -> :integer
    r':' -> :colon
    r',' -> :comma
    r'true|false' -> :boolean
    r'\s+' -> null
  }
  parser<ll1> {
    $json = $obj | $list
    $obj = :lbrace list($key_value_pair, :comma) :rbrace -> JsonObject(values=$1)
    $key_value_pair = $key :colon $value -> KeyValue(key=$0, value=$2)
    $key = :string | :integer
    $value = :string | :integer | :boolean | $obj | $list
    $list = :lsquare list($value, :comma) :rsquare -> JsonList(values=$1)
  }
}
"""

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

json_parser = hermes.compile(grammar, module='json_parser', debug=False)
tree = json_parser.parse('{"a": 1, "b": [1,2,3], "this is a key":[false, true, false]}')
#print(tree.dumps(indent=2, color=json_parser.term_color))
#print(tree.dumps(color=json_parser.term_color))
print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))

simple_parser = hermes.compile(simple, module='simple_parser', debug=False)
tree = simple_parser.parse('aaabbb')
print(tree.dumps(indent=2, color=json_parser.term_color))
#print(tree.dumps(color=json_parser.term_color))
#print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))
