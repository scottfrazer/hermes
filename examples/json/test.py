import hermes

with open('json.hgr') as fp:
    json_parser = hermes.compile(fp, module='json_parser', debug=False)
tree = json_parser.parse('{"a": 1, "b": [1,2.3e4,-3E-4], "this is a key":[false, true, false]}')
print(tree.dumps(indent=2, color=json_parser.term_color))
print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))
