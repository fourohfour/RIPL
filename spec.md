# RIPL Specification

RIPL is a simple programming language designed for transpilation into turing-machine style esolangs.

Here are detailed some of the key concepts in RIPL.

**Points and Literals**

A point is a named, abstract representation of a memory location. Points can be bound to data as shown below:

    x ! 42       // Set the point 'x' to the literal integer 42
    z !          // Set the point 'z' to the literal integer 0

Points are global in scope. Points have fixed length and generally implementations will fix the location of points in memory at compile time.

The exclamation point is used to set data into a point. The choice to not use a standard assignment operator (i.e. '=') is a deliberate one to discourage programmers from treating points like variables in other languages. Although they act like variables they are better thought of as similar to pointers.

The exclamation point can be followed by data, or alternatively nothing at all. Setting nothing to a point is equivalent to setting it to the integer literal `0`.

Other data can also be represented literally.
The following are acceptable data literals:

    19           // Literal integer 19
    {1, 2, 3}    // Literal structure containing the integers 1, 2, and 3
    
    'J'          // Literal character 'J'
    "vanwall"    // Literal string "vanwall"

    true         // Literal boolean value true
    false        // Literal boolean value false

A character literal is semantic sugar for a literal integer with that character's Unicode codepoint.
A string literal is semantic sugar for a literal structure, with an integer for each character's Unicode codepoint.

Integer values can be coerced to booleans but this is undefined behaviour and may vary depending on the language being transpiled to. Generally, positive values will coerce to true, and zero / negative values will coerce to false.

**Relational Expressions**

Relational expressions can be evaluated at runtime to act as conditionals. They work as you would expect. Convention states that they should be enclosed in parentheses to indicate how they should be evaluated.

    x ! 100

    (x <  150)   // Less than                 - Evaluates to true
    (x >  150)   // Greater than              - Evaluates to false
    (x =  100)   // Equal to                  - Evaluates to true
    (x ~= 100)   // Not Equal to              - Evaluates to false
    (x <= 100)   // Less than or Equal to     - Evaluates to true
    (x >= 99 )   // Greater than or Equal to  - Evaluates to false

**Arithmatic and Point Retrieval**

Arithmatic can be performed using integer literals and integer points. Note that characters and integers are equivalent so can be used interchangably. The use of Arithmatic on structures is undefined behaviour.

When working with points, it must be remembered that after transpilation a point represents a location along a tape or similar data structure. Therefore, a point must be accessed. This is done with an ampersand. The use of an ampersand instead of an asterisk is intentional, and the reasons for this choice are twofold.

 * A point must be accessed by physically going to that location on the tape; it cannot simply be retrieved as is the case with standard pointers.
 * Symbols should have one and only one semantic meaning, regardless of context, to disambiguate code and simplify implementation of the language.

Some examples of arithmatic and point retrieval are given below:

    x      !  2  +  6    // Set point x to 8 using addition
    y      !  2  *  2    // Set point y to 4 using multiplication
    z      ! &x  - &y    // Set point z to 4 using subtraction of other points
    result ! &z  /  2    // Set point result to 2 using floor division


**Procedures**

Procedures are utility statements primarily to similify common tasks or allow access to features of a target language. Therefore, some procedures may only be available when transpiling to a particular target language.

Procedures are signified with an `@` sign.

Some example procedures are given below. These are not guarunteed to be implemented for any specific transpilation target but instead serve as demonstration of the procedure call syntax.

    c ! @input   // Set point c to a character from stdin

    @output  22  // Output the integer 22 to stdout

    @exit &e     // Exit with the exit code given at the point 'e'


**Control Flow**

TODO
