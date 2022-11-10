'''
Part 6 will be short, we'll add the ability to get our source code from an external file:

python3 6.x-forth.py ../../../../forth_samples/x-b/3.xf 
'''
import traceback
import sys
import os.path

# if an argument was passed to the file
if len(args := sys.argv[1:]) > 0:
    # get the argument
    filename = args[0]
    if filename.endswith('.xf'):
        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                src = f.read()
            # now we'll add a location so we can know what file an error is coming from
            location = f'{filename}: '
        else:
            # source file not found error
            print(f'ERROR: {filename}: Source File Not Found')
            # exit with error
            sys.exit(1)
else:
    # if we're using internal source use an empty location
    location = ''
    # Forth source code
    src = '2 3 + .' # 5.0
    # uncomment these other sources to try out more complex programs
    # src = '1 2 + show dup + show 2 * .s 15 > . 10 10 .s drop .s'
    # output
    # 3.0
    # 6.0
    # <1> 12.0 ok
    # 0.0
    # <2> 10.0 10.0 ok
    # <1> 10.0 ok
    #src = '''
    #    1 2 > 0 == .
    #    15 dup + .
    #    1 2 3 4 5 .s
    #    drop drop drop .s
    #'''
    # output
    # 1.0
    # 30.0
    # <5> 1.0 2.0 3.0 4.0 5.0 ok
    # <2> 1.0 2.0 ok

# custom X Forth exception
class XForthException(Exception):
    pass

# the ValueType object represents the datatype of a Forth value, for now we'll only have two:
# Undefined and numbers
# we'll use Python's enum class to construct it
from enum import Enum, auto

class ValueType(Enum):
    Undefined = auto()
    Number = auto()

# we'll use a dataclass for the value. We could (maybe should) just use tuples, but it will be nice to have named fields
from dataclasses import dataclass
from typing import Any

@dataclass
class Value:
    type: ValueType = ValueType.Undefined
    value: Any = None

# operators
OPERATORS = [
    # math
    '+',
    '-',
    '*',
    '/',
    # logic
    '<',
    '>',
    '==',
    '!=',
]

# we'll use a lookup table for the more complex words
# we're going to do some weird code here to get around Python's forward declaration requirements
# because Python is interpreted line by line, you cannot refer to a function before calling it unless it is inside a function
# so to avoid rearranging and interleaving all our variables and functions, we must make sure to wrap our function calls inside lambdas
# the actual lookup table for the function
FUNC_TABLE = {
    '.':    lambda: stack_print(),
    '.s':   lambda: stack_display(),
    'drop': lambda: stack_drop(),
    'dup':  lambda: stack_dup(),
    # note that we wrap the call to stack_print in a lambda so we can pass false for the consume argument
    'show': lambda: stack_print(consume=False)
}

# we'll also combine the operators and function like words into a single list for easy lookup
WORDS = [
    *OPERATORS,
    # note that we spread only the keys from FUNC_TABLE
    *FUNC_TABLE.keys()
]

# the size of the stack
STACK_CAPACITY = 1024
# generate STACK_CAPACITY values
stack = [Value() for _ in range(STACK_CAPACITY)]
# NOTE that the following will not give you what you want
# stack = [Value()] * STACK_CAPACITY
# this code will actually contain a list of the same instance of Value
# but the code above will create a unique instance for each entry
stack_top = -1

# a bit of extra documentation
from typing import List

def tokenize(src: str) -> List[str]:
    '''tokenize breaks up a source string into a series of tokens, represented as a list of strings'''
    # remove leading and trailing whitespace
    src = src.strip()
    # the list of tokens to return
    # in X-B a token is just a string and thus tokens is a list of strings
    tokens = []
    # we will use this to build up tokens comprised of more than one char
    token = ''

    for index, char in enumerate(src):
        # if we get a space we want to end the last token and add it to the token list
        if char.isspace():
            # only add the token if it isn't empty
            if token != '':
                # add the token to the list
                tokens.append(token)
            # reset the token to an empty string
            token = ''
        else:
            # append the character to the token string
            token += char
            # if we are at the end of the src we should add the token to the list
            if index >= len(src)-1:
                tokens.append(token)
    return tokens

def error_stack_underflow(word: str):
    '''Stack underflow happens when there aren't enough arguments for a word'''
    raise XForthException(f'{location}ERROR: {word} : Stack underflow')

# we'll use this to display what is currently on the stack
def stack_display():
    '''stack_display displays the state of the stack in the format:
    <count of values> val1 val2 ... ok'''
    # how many elements are on the stack
    count = stack_top + 1
    # first we'll print the number of values on the stack
    print(f'<{count}> ', end='')
    # only try to print if there is at least 1 value on the stack
    if count >= 1:
        for i in range(count):
            value = stack[i]
            # print the values separated by spaces
            print(f'{value.value} ', end='')

    # Forth ends its stack display with ok, let's do this
    print('ok')

def stack_drop():
    '''stack_drop removes an element from the top of the stack

    errors:
        Stack underflow'''
    global stack_top
    # you can't drop something if it doesn't exist!
    if stack_top < 0:
        error_stack_underflow('drop')
    # to drop we just need to decrement the top
    stack_top -= 1

def stack_dup():
    '''stack_dup duplicates the value on the top of the stack'''
    global stack_top
    # we need at least 1 argument
    if stack_top < 0:
        error_stack_underflow('dup')
    # get the current top value
    val = stack[stack_top]
    # incrememnt the stack top
    stack_top += 1
    # copy the values to the new value at the top of the stack
    stack[stack_top].type = val.type
    stack[stack_top].value = val.value

# by passing a bool to stack_print we can use it for both . and show
def stack_print(consume: bool = True):
    '''stack_print displays the value on the top of the stack. If consume is True it will remove the top value from the stack, otherwise it will not.

    Used for both . and show

    errors:
        Stack underflow'''
    global stack_top
    # print requires 1 argument so the stack_top must be >= 0
    if stack_top < 0:
        # if there aren't enough arguments that is a stack underflow
        error_stack_underflow('.')
    # get the value from the top of the stack
    val = stack[stack_top]
    # if we should consume it, decrement the stack
    if consume:
        stack_top -= 1
    # print the value
    print(val.value)

# helper to check if a string is a number
def is_number(src: str) -> bool:
    '''A simple helper to check if a string is a number'''
    try:
        return float(src)
    except:
        return None

def interpret(tokens: List[str]):
    '''interpret interates and executes the tokens passed to it'''
    # declare global access to stack_top
    global stack_top

    # iterate through each token
    for token in tokens:
        # numbers
        if (number := is_number(token)) != None:
            # increment stack top
            stack_top += 1 
            # set the type to number
            stack[stack_top].type = ValueType.Number
            # assign the value
            stack[stack_top].value = number
        # operators
        elif token in WORDS:
            if token in OPERATORS:
                # all current operators require 2 arguments so we can check if the stack top is < 1
                # if stack top is >= 1 there are 2 or more arguments on the stack
                if stack_top < 1:
                    error_stack_underflow(token)
                # get arguments, note that the second argument is on the top of the stack and the first is under it:
                # push 2
                # push 3
                # [ 2 3 ]
                # b = 3
                # a = 2
                b = stack[stack_top]
                # decrement the stack_top to pop the value
                stack_top -= 1
                # decrement the stack_top to pop the value
                a = stack[stack_top]
                stack_top -= 1

                result = None

                # perform the correct operation based on the operator
                # math operators
                if token == '+':
                    result = a.value + b.value
                elif token == '-':
                    result = a.value - b.value
                elif token == '*':
                    result = a.value * b.value
                elif token == '/':
                    # for now if we try to divide by zero we'll just get zero
                    if b.value == 0:
                        result = 0.0
                    else:
                        result = a.value / b.value
                # boolean operators
                # note that we want to convert the bool value to a float 1.0 or 0.0
                elif token == '<':
                    result = 0.0 if a.value < b.value else 1.0
                elif token == '>':
                    result = 0.0 if a.value > b.value else 1.0
                elif token == '==':
                    result = 0.0 if a.value == b.value else 1.0
                elif token == '!=':
                    result = 0.0 if a.value != b.value else 1.0

            # push the value back onto the stack 
            # first increment stack_top
                stack_top += 1
                # assign the result to the value
                stack[stack_top].value = result
                # assign the number type
                # for now the values are always numbers, but this will become important when we add more datatypes later on
                stack[stack_top].type = ValueType.Number
            # function words
            else:
                # lookup and call the function from FUNC_TABLE
                FUNC_TABLE[token]()
        else:
            raise XForthException(f'{location}ERROR: Undefined token {token}')

if __name__ == '__main__':
    tokens = tokenize(src)
    print(f'** TOKENS **\n{tokens}')

    print(f'\n** INTERPRET **')
    try:
        interpret(tokens)
    except XForthException as e:
        print(e)
    except:
        print('**DEV ERROR**') 
        traceback.print_exc()
