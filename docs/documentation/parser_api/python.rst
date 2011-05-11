Python Parser API
=================

This section describes the contents of the code that Hermes generates.  All of the classes and all methods of the generated parser are documented here.

.. py:module:: Parser

.. py:class:: Parser( id )

.. py:function:: Parser.parse( iterable, entry )

   Returns a *ParseTree* object that represents the parsing of the iterable containing *Terminal* objects against your grammar specification.  The entry point is a string representation of the starting token.

   On a syntax error this method will raise an exception.

.. py:class:: NonTerminal( id )

  This object is used as the interior nodes in *ParseTree* objects.  It contains two attributes, id and string.

.. py:class:: Terminal( id )
  
  This object is the simplest object that can be used as for the parse() function on the parser.  This class can be extended to create
  
.. py:function:: Terminal.getId()

   Returns the ID of the terminal

.. py:function:: Terminal.toAst()

   Returns a representation of this object as an abstract syntax tree.  In most cases, this will simply ``return self``.
   
.. py:class:: ParseTree( nonterminal )

.. py:function:: ParseTree.add( tree )

   Add a child node to this parse tree.  Child node will be added at end of list.

.. py:function:: ParseTree.toAst()

   Convert this object to an abstract syntax tree

.. py:class:: Ast( name, attributes )

   Object representing an abstract syntax tree.  the ``name`` parameter is a string identifying the type of AST and the attributes is a dictionary of attribute name (string) to attribute value.

.. py:function:: Ast.getAttr( attribute )

   Returns the value of the attribute specified.

