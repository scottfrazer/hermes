import java.util.List;

public class JavaTest {
    public static void main(String[] args) {
        TestParser parser = new TestParser();
        try {
            List<TestParser.Terminal> terminals = parser.lex(
                "{\"a\": 1, \"b\": [1,2,3], \"this is a key\":[false, true, false]}",
                "<string>"
            );
            System.out.println("Tokens:\n");
            for (TestParser.Terminal terminal : terminals) {
                System.out.println(terminal.toPrettyString());
            }

            System.out.println("\nParse Tree:\n");
            TestParser.ParseTree tree = parser.parse(
                new TestParser.TokenStream(terminals)
            );
            System.out.println(tree.toPrettyString());

            System.out.println("\nAbstract Syntax Tree:\n");
            TestParser.Ast ast = (TestParser.Ast) tree.toAst();
            System.out.println(ast.toPrettyString());
        } catch(TestParser.SyntaxError e) {
            System.err.println(e);
        }
    }
}
