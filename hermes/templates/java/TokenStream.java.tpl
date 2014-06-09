{% if java_package %}
package {{java_package}};
{% endif %}

import java.util.ArrayList;
import java.util.List;
import java.util.Formatter;
import java.util.Locale;

public class TokenStream extends ArrayList<Terminal> {

  private int index;

  public TokenStream(List<Terminal> terminals) {
    super(terminals);
    reset();
  }

  public TokenStream() {
    reset();
  }

  public void reset() {
    this.index = 0;
  }

  public Terminal advance() {
    this.index += 1;
    return this.current();
  }

  public Terminal current() {
    try {
      return this.get(this.index);
    } catch (IndexOutOfBoundsException e) {
      return null;
    }
  }

  public Terminal last() {
    return this.get(this.size() - 1);
  }

}
