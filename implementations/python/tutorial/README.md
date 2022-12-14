# X-Forth Tutorial
Follow along with the development of a Python implementation of X-Forth. Each lesson builds incrementally on the last in manageable steps.

## X-Forth.py
The file x-forth.py represents the latest tutorial completed and thus the most feature complete version of the python implementaiton.

## Tutorial Index
### X-B (basic)
* [1](src/1.x-forth.py)  - A simple tokenizer with hardcoded Forth source
* [2](src/2.x-forth.py) - A simple interpreter that can push numbers to the stack and display the stack contents
* [3](src/3.x-forth.py) - Adding math operators to the interpreter
* [4](src/4.x-forth.py) - Adding logic operators to the interpreter
* [5](src/5.x-forth.py) - Finish X-B by Adding some basic stack manipulation and display words
### X-1 (External/Variable Source Code)
* [6](src/6.x-forth.py) - X-1 allows us to read source code from external files
### X-2 (Symbols)
* [7](src/7.x-forth.py) - Implement Symbols which are a building block for many other extensions
### X-3 (Bools)
* [8](src/8.x-forth.py) - Implement the boolean literals `True` and `False`
### X-4 (Variables)
* [9](src/9.x-forth.py) - Implement variables and constants to read and write from memory locations referred to by name
<!--Consider breaking 9 up into smaller lessons, it is quite a big change-->
* [10](src/10.x-forth.py) - Implement `!` and `@` to read and write
### X-5 (String Support)
* [11](src/11.x-forth.py) - Beginning string support. First we'll modify the tokenizer to tokenize strings as a single token
* [12](src/12.x-forth.py) - Add the string type and modify the interpreter to recognize and evalute string tokens by pushing them to the stack
* [13](src/13.x-forth.py) - Add some words to work with strings
* [14](src/14.x-forth.py) - Finish by allowing escape sequences in strings
### X-6 (Include) - X-6.B (Mid Interpretation Includes)
* [15](src/15.x-forth.py) - Implement including other x-forth files
