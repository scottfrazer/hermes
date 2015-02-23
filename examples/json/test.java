import java.util.List;
import java.util.regex.*;

public class test {
    public static void main(String[] args) {
        JsonParser parser = new JsonParser();
        try {
            List<JsonParser.Terminal> terminals = parser.lex(
                "{\"a\": 1, \"b\": [-1,2e4,-0.003e4,0], \"this is a key\":[false, true, false]}",
                "<string>"
            );
            System.out.println("Tokens:\n");
            for (JsonParser.Terminal terminal : terminals) {
                System.out.println(terminal.toPrettyString());
            }

            System.out.println("\nParse Tree:\n");
            JsonParser.ParseTree tree = parser.parse(
                new JsonParser.TokenStream(terminals)
            );
            System.out.println(tree.toPrettyString());

            System.out.println("\nAbstract Syntax Tree:\n");
            JsonParser.Ast ast = (JsonParser.Ast) tree.toAst();
            System.out.println(ast.toPrettyString());
        } catch(JsonParser.SyntaxError e) {
            System.err.println(e);
        }
    }
}
