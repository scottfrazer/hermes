import hermes

with open('xml.hgr') as fp:
    xml_parser = hermes.compile(fp, module='xml_parser', debug=False)
tokens = xml_parser.lex('<a x="1" y="2"><b><c>hello</c><d>world</d></b></a>', '<string>')
for token in tokens:
    print(token)
#tree = xml_parser.parse('<a x="1" y="2"><b><c>hello</c><d>world</d></b></a>')
#print(tree.dumps(indent=2, color=json_parser.term_color))
#print(tree.toAst().dumps(indent=2, b64_source=True, color=json_parser.term_color))
