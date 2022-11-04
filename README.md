# X-Forth
X-Forth is a small Forth specification meant to be used in compiler projects. You can likely implement the basic X-forth in a couple hours or less.
```py
2 3 + .s
# <2> 2.0 3.0 ok
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
#### data types
- number - all numbers are treated as double precision floats. X-B does not have a boolean type and false is treated as 0.0 while true is 1.0
#### words
- +, -, *, / - The basic math operators
- <, >, ==, != - The basic logic operators
- . (dot) - print and consume the value on the top of the stack
- .s - print the whole stack to the console without consuming it in the format: \<count of values> val1 val2 ... ok
- drop - remove the top value from the stack
- dup - duplicate the top value on the stack
- show - print the value on the top of the stack without consuming it
#### errors
- Unknown token - present this error when we find an invalid token in the source code
    - format `ERROR: Unknown token <token>`
- Stack underflow - present this error when there aren't enough values on the stack for a word
    - math and logic operators require 2 arguments
    - . (dot) and dup require 1 argument
    - format `ERROR: <word name>: Stack underflow`
#### quirks
- what happened!? - X-B contains virtually no error handling at the compiler level with the exception of throwing an error when encountering an unknown token. There are no stack traces, line numbers in errors or other helpful bits of error context.
- hardcoded source - X-B's source code is hardcoded in the program, see [X-1](#-x-1-(external/variable-source-code)) (External Source Code) to get variable source code

### X-1 (External/Variable Source Code)
Acquire the source code from an external file. Receive an external file path on the command line, validate its existence and read its contents into the src variable. 

X-Forth files use the `.forth` extension

#### errors
- Source file not found - The passed file path could not be found
    - format: `ERROR: <source path>: Source File Not Found`

### X-2 (REPL)
Add a Read Eval Print Loop. TODO

### X-3 (Custom Words)
#### X-3.A (Constant Custom Word)
X-3.A implements custom words that cannot be overriden. Attempting to redefine a word that already exists will result in a `Word redefinition` error 

#### errors
- Word Refinition - you attempted to redefine an existing word
    - format: `ERROR: <word name> : Word Redefinition`
#### X-3.B (Redefinable Custom Words)
X-3.B implements custom words that can be redefined. Defining a word that already exists will overwrite its entry in the global lookup table.
### X-4 (Bool support)
Support for boolean types. This is mostly cosmetic as they should be treated as numbers under the hood. The words `true` and `false` should be aliases for `greater than 0` and `0` respectively, effectively making them constants. Though they are mostly aliases, it can be helpful to give them a dedicated boolean type even though they are stored numerically so you can differentiate them from numbers for printing.

<!-- 0 should be true and anything else false? This would integrate well with errors. Errors could similarly be aliases where 0 represents no error and positive numbers represent specific errors like an enum. This would allow things like:

: work 1 ; # something went wrong

work if drop "it worked!" . else "something went wrong, error # " swap to-string concat .;

Maybe I'm over thinking it. But errors should definitely be enums. I think this makes sense actually, 0 is true and anything else is error, that way the first value of an enum/error set is always no error
-->
### X-5 (String support)
X-5 brings string support. Specifics about the string implementation like: immutability vs mutability, pascal style (length prefixed) vs c style (null terminated) are left to the implementation to decide.
#### required words
* length ( string -- string number )- gives count of characters in the string.
* append ( string string -- string ) - appends one string to another
* to-string ( number -- string ) - converts a number into a string
    * should be implemented for each primtive datatype you included in your Forth. So if you've implemented X-5 (Bool), you should also provide a bool conversion that returns `"true"` or `"false"`
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
    * Immplementation
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
### Third Party
If you create an X-Forth please let me know, I'd love to link to it! Any language is great!

## For Fun
This project was created to allow me to play with and compare different languages and to explore different aspects of programming languages and compilers like: interpreters, compiling to native code, assembly, virtual machines and more. Even if you're not interested in Forth, you might be interested in the ways similar things are implemented in the different languages used here. 