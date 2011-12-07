#include "{{}}.h"

{% if addMain %}
int main(int argc, char * argv[])
{
  TERMINAL_T tokens[] = {
    {% for terminal in initialTerminals %}
    {TERMINAL_{{terminal.upper()}}, "{{terminal.lower()}}"}
    {% endfor %}
  }
}
