<!--reference
 Easy Forth: https://skilldrick.github.io/easyforth/#conditionals-and-loops
 Forth in y minutes: https://learnxinyminutes.com/docs/forth/
-->
# X-Forth
X-Forth is a small specification for a Forth like language meant to be used in compiler projects. You can likely implement the basic X-forth in a couple hours or less.
```py
a: 10 var
b: 5  var
a @ b @ + . # 15.0
dup * .     # 225.0
drop .s     # <0> ok
5 6 + 3 4   # <3> 11.0 3.0 4.0 ok
```
## Tutorial
There are ongoing (WIP) tutorials that accompany the Python implementation [here](implementations/python/tutorial).


## The Name
X-Forth is so named because the X refers to a few aspects and goals of the project:
- X-Forth - where X == implementation language, ex. Go-Forth, Dart-Forth, JS-Forth etc.
- X for eXample - X-Forth is meant to be used as an example project to play with. The various extensions of X-Forth provide smaller sub projects to help you explore your language of choice as well as broader compiler/language features.
- X for eXtended - X-Forth is intentionally designed as a series of extensions to a very primitive language

Similar to the Scheme language, X-forth specifies language add-ons which can be implemented to extend the language, designated as `X-<number> (description)`. The basic version of X-Forth is denoted as `X-B (Basic)` and contains a bare bones interpreter with very basic mathmatical and logical operators along with a few built in words for display and stack manipulation. The first few extensions are designed to provide easily manageable incremental projects.

## Why A Forth?

I believe concatenative stack based langauges are the most simple languages to write compilers for, even simpler than the more popular lisp, though they may be more unintuitive to program in than a traditional language. You can learn a lot and have fun focusing on features rather than parsing a complex langauge. If you're interested in something that is more similar to a traditional C like language, I'll be working on a sister project to this based on Basic called `X-Basic`.

It is very fast to write a Forth and it can even easily bootstrap itself from assembly as seen in [Jones Forth](https://github.com/nornagon/jonesforth/blob/master/jonesforth.S)


## Current Extension Specs

### X-B (Basic)
The most basic version of X-Forth. It contains only a few operators and functions, collectively known as `words`. The tokenizer is very primitive and effectively makes the language white space significant since all tokens are separated on white space.
#### required types
- Number - all numbers are treated as double precision floats. X-B does not have a boolean type and false is treated as 0.0 while true is 1.0
#### words
- +, -, *, / - The basic math operators
- <, >, ==, != - The basic logic operators
- . (dot) - print and consume the value on the top of the stack
- .s - print the whole stack to the console without consuming it in the format: \<count of values> val1 val2 ... ok
- drop - remove the top value from the stack
- dup - duplicate the top value on the stack
- show - print the value on the top of the stack without consuming it
#### errors
- Undefined token - present this error when we find an invalid token in the source code
    - format `ERROR: Undefined token <token>`
- Stack underflow - present this error when there aren't enough values on the stack for a word
    - math and logic operators require 2 arguments
    - . (dot) and dup require 1 argument
    - format `ERROR: <word name>: Stack underflow`
#### quirks
- what happened!? - X-B contains virtually no error handling at the compiler level with the exception of throwing an error when encountering an Undefined token. There are no stack traces, line numbers in errors or other helpful bits of error context.
- hardcoded source - X-B's source code is hardcoded in the program, see [X-1](#x-1-(external/variable-source-code)) (External Source Code) to get variable source code

### X-1 (External/Variable Source Code)
Acquire the source code from an external file. Receive an external file path on the command line, validate its existence and read its contents into a source string variable. 

X-Forth files use the `.forth` extension

#### errors
- Source file not found - The passed file path could not be found
    - format: `ERROR: <source path>: Source File Not Found`
#### spec
* numbers - numbers are machine word/register sized floating point.
* booleans - in X-Forth booleans are numeric values where 0 is true and anything else is false. This is odd compared to C languages, but it aligns with the design ofr errors wherein an error can be represented as an enum with the first value 0 representing no error, see [X-7 (errors)](#x-7-(errors)) for more. Instead of thinking in terms of true or false, we think in terms of "did an error occur" where `0` means no error occured and any other number denotes that some error occured and which one

### X-2 (Symbols)
Symbols are are words whose value equates to a hash value, they are similar to symbols found in Ruby. Syntactically a symbol is a word that ends with `:`, for example: `dup` is the word dup, and when this is encountered it be called immediately but, `dup:` is a symbol which instead of calling the `dup` word pushes a hash value to the stack. Symbols are important for things like variables, lookup tables and passing words around as values. Symbols can be converted to and from strings if you have implemented X-5 (String Support).
#### spec
Symbol is the type of symbols and their value should be a tuple (or equivalent) of the word as a string and its hash value. 
#### required overloads
* X-5 (String support)
    * to-string ( symbol -- string ) - converts a symbol into a string without the `:` suffix
    * to-symbol ( string -- symbol ) - converts a string into a symbol
#### required types
* Symbol

### X-3 (Bools)
Support for boolean types. This is mostly cosmetic as they should be treated as numbers under the hood. The words `True` and `False` should be aliases for `0` and `1` respectively, effectively making them constants. Though they are mostly aliases, it can be helpful to give them a dedicated boolean type even though they are stored numerically so you can differentiate them from numbers for printing. 

As mentioned in the X-B section, the use of `0` for true and `1` for false differs from traditional C-like languages because it is designed with error handling in mind. Instead of thinking in terms of true or false we think in terms of asserting whether or not an error occured with `0` meaning no error occured and any other number not only denoting that an error occured, but which one. By convention, user defined errors should be `>= 1 <= MAX NUMBER`, while negative values are used for built in errors.
#### required Types
* Bool - can be either True (0) or False (1)
#### required words
* True `True: 0 con` - constant == `0`
* False `False: 1 con` - constant == `1`
#### required overloads
<!-- TODO
* to-bool (number -- bool) - converts`0` to `True` and anything else to `False`
* to-number ( bool -- number ) - converts `True` to `0` and `False` to `1`
-->
* X-5 (String support)
    * to-string ( bool -- string ) - converts a bool into either `"True"` or `"False"`

### X-4 (Variables) requires X-2 (Symbols)
Implements both variables and constants. X-Forth uses `var` and `con` for variables and constants respectively. As arguments var and con take a value and a symbol.
```py
num: 10 var # store 10 into the variable num
n2: 13 con # define n2 as the constant 13
```
<!--`var` has a second verson wherein you can forward declare a variable with no value and then assign to it later. -->In order to assign a value to a variable/constant use the `!` (write) word:
```py
num: var # num variable created with its value set to 'Undefined'
num 10 ! # write 10 to it
```
To get the value of a variable use the `@` (read) word:
```py
num @ # 10
```
Like a traditional Forth, the usage of the variable name pushes its address to the stack<!--, however unlike a traditional Forth the `<name>: var` declaration also pushes the address to the stack, which allows assigning to a variable while only writing its name once: `` -->. `con` is the same as `var` but internally it makes use of some sort of `is_set` flag denoting whether or not the constant has been set. It must be set before use and once set it cannot change.

Unlike variables, constants do not push their address to the stack, and instead just directly push their value, thus you do not use `@` with constants.
#### required words
* Undefined - represents an undefined value, errors will occur if you try to use an undefined value. This is a built in value and must be given its own type which is also `Undefined`
* var ( symbol any -- ) - If the top value is not a symbol, but the second value is, then the top value is assigned to the variable and the address is NOT pushed to the stack
    * ( symbol -- address) - If the top value is a symbol, then variable's value will be set to `Undefined`.<!-- and the address is pushed to the stack: `num: var # address of num variable is pushed to stack` -->
* con ( symbol any -- ) - con is exactly like the first overload of var except that its value cannot be changed and the words value rather than its address is pushed to the stack when the word is used 
* ! ( address any -- ) - writes the value on the top of the stack to the address
* @ ( address -- any) - reads and pushes the value at the address
```py
value1: 15 var
value2: 30 con
```
#### required types
* Address - represents an address, it is similar to a pointer and is an index into the program's memory.
* Undefined - the type of undefined variables
<!--
#### spec
* Memory - a contigous (optionally growable) block of memory should be allocated for each program. Variables should be names mapped to indices starting at `0` and this index should be used to index into the program's memory starting from the variable memory section. Python implementation example:
```py
# program memory
MEMORY_CAPACITY = 1024
memory = [None] *  MEMORY_CAPACITY

# variable lookup table
variables = {
    'num': {'index': 0, 'constant': False, 'set': True }
}

# start of variable memory
VAR_START = 500

# accessing the num variable
num = memory[VAR_START + variables['num']['index']]
```
-->
### X-5 (String support)
X-5 brings string support. Specifics about the string implementation like: immutability vs mutability, pascal style (length prefixed) vs c style (null terminated) are left to the implementation to decide.
#### required words
* length ( string -- string number ) - gives count of characters in the string.
* append ( string string -- string ) - string concatenation
#### required overloads
<!--* append ( string string -- string ) - overload `+` operator to work with strings for concatenation-->
* to-string ( number -- string ) - converts a number into a string
    * should be implemented for each primtive datatype you included in your Forth. So if you've implemented X-3 (Bool), you should also provide a bool conversion that returns `"True"` or `"False"`
* to-number ( string -- number ) - convert a string into a number
#### spec
X-Forth strings are defined using double quotes `"` which allows for the optional implementation of single char types.

### X-6 (Includes) requires X-5 (String support)
X-6 brings include support which allows including external Forth files. It works similarly to C's `include` and inserts the source code of another file at the location. `include` operates on a string path:
```nim
"./files/some_file.forth" include
```
`include` can be implemented to work at parse/compile time or during interpretation/runtime, this is implementation specific.
#### required words
* include (string -- ?) - extends the token stream with tokens from the passed file
    * note that we have ? as the return value because the state of the stack depends on the file included. If that file pushed a value as the last statement then that would apply to the current program
#### X-6.A (Pre Interpretation Include) 
X-6.A implements `include` before the interpretation phase. During the tokenizing step when adding a word to the token list, if the token is `include` then remove the previous token from the token list, verify that it starts with `"` (double quote) and ends with `.forth"`, and if so, verify the files existence, read the file into a string and then call the tokenize function recursively to aquire the tokens from that source code, then extend/spread these tokens into the current token list.
#### X-6.B (Mid Interpretation Include)
X-6.B implements `include` mid interpretation. This allows for dynamic loading of libraries and code which can change based on input during runtime. To implement `include` during interpretation you could modify the token stream, and its length. When encountering `include`, pop the last string from the stack, varify it is a valid path to a `.forth` file, read its source, tokenize it, then extend the token stream with these tokens and if needed modify the loop to account for the new length, then continue interpretation on the new tokens at the included site. 

### X-7 (Blocks)
Blocks are a unique construct in X-Forth and are similar to LISP lists. Blocks are denoted with square brackets `[]` and can contain any tokens: `[ 1 2 ]`, `[ 1 2 + ]`, `[ "hello" some-word ]`. Blocks are just lists of tokens which can be passed around and operated upon by words. Blocks serve as the basis for higher level constructs like custom words and control flow.

Blocks have multiple uses and provide different functionality based on the words used to operate on them:
* lists - blocks can be used as lists of data, similar to lists in Python or JavaScript, here is a block (list) of numbers : `[ 1 2 3 ]`
* tables - blocks can be used as lookup tables as well: `[ 0 10 1 20 ] 0 get # 10`
    * If you've implemented [X-2 (Symbols)](#x-2-(symbols)) you can get JavaScript like syntax: `[ a: 10 b: 20 ] a: get # 10`
* custom words - blocks in combination with [X-4 (Variables)](#x-3-(variables)) for the basis for custom words (see [X-6](#x-6-(custom-words)))aka functions: `add-five: [ 5 + ] con`
* anonymous functions - you can pass blocks around and execute them using the `call` and `apply` words:
```py
10 [ 5 + ] call # 15, call operates directly on the stack taking only a single block as an argument
[ 5 + ] [ 10 ] apply # 15, apply takes a block of arguments which will be pushed to the stack first and a block of instructions 
```
<!--
Now with variables and blocks you get custo words for free by assigning blocks to constants,
however you should consider allowing stack effect comments such as (n -- n) be part of the arguments to var and con and actually be stored somewhere, perhaps in a separate lookup table. Consider expanding the stack effect comment syntax to include multiline strings or comments

    add-five: [ 5 + ] ( n -- n
        "add-five adds five to its argument") con

I could parse out the stack effect into its args and its doc comment by simply splitting on " and then on -- to get input and output. This extension can extend custom words with the stack effect and the doc/help/see words to get the info about a word

### X-6 (Custom Words) requries X-4 (Variables), X-5 (Blocks)
#### X-6.A (Constant Custom Word)
Implements custom words that cannot be overriden. Attempting to redefine a word that already exists will result in a `Word redefinition` error 

#### errors
- Word Refinition - you attempted to redefine an existing word
    - format: `ERROR: <word name> : Word Redefinition`
#### X-6.B (Redefinable Custom Words)
Implements custom words that can be redefined. Defining a word that already exists will overwrite its entry in the global lookup table. This implementation aligns with more traditionals Forths wherein a dictionary of words is searched linearly from the end.
-->
### X-8 (If) requires X-7 (Blocks)
### X-9 (Loop) requires X-7 (Blocks)
TODO
### X-10 (Word Documentation)
X-10 brings the ability to add documentation to words with stack effect comments: `add-five: [ 5 + ] ( n -- n "adds 5 to n" ) con`. This stack comment is a special type of comment that it associated with the word and can be looked up with the words `help`, `sig`
<!-- 0 should be true and anything else false? This would integrate well with errors. Errors could similarly be aliases where 0 represents no error and positive numbers represent specific errors like an enum. This would allow things like:

: work 1 ; # something went wrong

work if drop "it worked!" . else "something went wrong, error # " swap to-string concat .;

Maybe I'm over thinking it. But errors should definitely be enums. I think this makes sense actually, 0 is true and anything else is error, that way the first value of an enum/error set is always no error
-->
### X-11 (Errors)
TODO
### X-12 (REPL)
Add a Read Eval Print Loop. TODO
### X-13 (Comments)
X-Forth uses `#` for single line comments like Python. You can safely ignore any tokens beginning with `#`. 
### X-14 (Event Loop) requires X-4 (Variables)
X-Forth uses a simple event loop in which the X-Forth interpreter runs two (or more) execution contexts (threads, coroutines or otherwise) with two (or more) interpreters, one for the main program denoted the `Main Context`, and another (or multiple) for the non bocking execution of asynchronous tasks, called the `Background Context`. The `Background Context` should have an event queue which the `Main Context` can push jobs to and which the `Background Context` will constantly poll
### X-15 (Memory) requires X-4 (Variables)
Memory is introduced in X-4 (Variables) to implement user defined variables, but it is also used heavily for the X-17 Graphics extension and potential others. The size of the memory (and graphics) are up to the user. The memory should be a contigous array or linked list of contiguous blocks with portions dedicated to variables (X-4), keyboard input (X-16), screen pixels (X-17), and a data section (X-18)
### X-16 (Keyboard Input) requires X-14 (Event Loop), X-15 (Memory)
Allows for Keyboard input, both block and non-blocking
### X-17 (Graphics) requires X-16 (Keyboard Input)
X-16 brings a simple pixel buffer based graphics API inspired by BASIC. The program memory array is used heavily for the graphics api and a portion of it is dedicated to the screen memory. The size of the screen is up to the implementation, recommended sizes are: 256x240
### X-17 (Data section), X-14 (Memory)
TODO
### X-18 (With) requires X-4 (Variables)
With binds values on the stack to variable names temporarly for the lifetime of the top block passed to it: `10 5 [ a: b: ][ + ] with  # 15`. After execution of its block, the variables disappear and do not pollute the global scope.
### X-19 (Builtin Words 1)
This extension adds more stack words that are normally seen in Forths.
#### required words
* over ( a b -- a b a ) - copies the second stack value to the top of the stack
* swap ( a b -- b a ) - switch positions of the top two stack values
* rot ( a b c -- c b a ) - swap the first and third values on the stack, rotating them around the second value. Note that this word behaves differently than the rot word seen in traditional Forths
* grab ( a+ n -- a#n ) - given some values on the stack and a number at the top, copy value at index n (starting at 0) to the top.
#### required words
* with ( block block -- ? )
### X-? (Bytecode)
Stores X-Forth into an efficient Bytecode format. Values should be Nan Boxed or Pointer Tagged. TODO
### X-? (X-Forth Machine) requires X-? (Bytecode)
The X-Forth Machine is a virtual Forth machine, meant to be bootstrapped from native code such as Assembly, C for desktop or JavaScript or WASM in the browser. The XFVM (X-Forth Virtual Machine) posesses a fixed amount of memory used for variables, input/output, graphics and data storage. TODO 
<!--The exact specs of the machine in regards to memory can vary depending on the host, however, you will find some recommended specs to get you started:
#### Limited Hardware 1 (WIP)
This XFVM is modeled after the chip 8 virtual machine. TODO
#### Limited Hardware 2 (WIP)
This XFVM is based on the specs of the Nintendo Entertainment System (NES):
* 16 bit - machine words are 16 bits
* numbers are 16 bit integers, no floats
* 40 KB program data - This includes the Forth program itself, plus any data such as sprites or music and should be a `.xfb` X-Forth Binary file. Your Forth program must not exeed this size
* 2KB Memory - 
    * 500 B stack
    * 1590 B variable space
    * 10 bytes read only memory for 10 keys, representing the 10 buttons on an NES controller
        * up
        * right
        * down
        * left
        * select
        * start
        * A
        * B
        * L Button
        * R Button
* 56 colors available
* 256x240 screen (61,440 bytes) each of which can hold a value of 0 to 55 used to index into the 56 color palette
-->
<!--
## Suites
Suites are collections of Extensions which represent packages of functionality and can be used to describe the feature level of an X-Forth implementation

### S-1 (Turing)
Implementing S-1 means you have implemented a completely turing complete implementation of X-Forth. TODO
#### required extensions
* X-B (Basic)
* X-2 (Variables)
* X-? (If Statements)
* X-? (Loops)

### S-? (Limited Hardware)
TODO
-->
## Implementations
There are several implementations of X-Forth created along with the project in varying stages of completion and extension implementation. All implementations listed implement at least X-B: 
### Dart
* [phillvancejr / x-forth-dart](implementations/dart)
    * [X] X-B (Basic)
### Go
* phillvancejr / x-forth-go TODO
    * [ ] X-B (Basic)
### Python
* [phillvancejr / x-forth-py](implementations/python/tutorial)
    * [X] X-B (Basic)
    * [X] X-1 (External/Variable Source Code)
    * [X] X-2 (Symbols)
    * [X] X-3 (Bools)
    * [X] X-4 (Variables)
### Third Party
If you create an X-Forth please let me know, I'd love to link to it! Any language is great!

## For Fun
This project was created to allow me to play with and compare different languages and to explore different aspects of programming languages and compilers like: interpreters, compiling to native code, assembly, virtual machines and more. Even if you're not interested in Forth, you might be interested in the ways similar things are implemented in the different languages used here. 