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
Add a Read Eval Print Loop.

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
### Third Party
If you create an X-Forth please let me know, I'd love to link to it! Any language is great!

## For Fun
This project was created to allow me to play with and compare different languages and to explore different aspects of programming languages and compilers like: interpreters, compiling to native code, assembly, virtual machines and more. Even if you're not interested in Forth, you might be interested in the ways similar things are implemented in the different languages used here. 