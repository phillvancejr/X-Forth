'''
Part 4 is a short lesson in which we will add some basic logic operators: <, >, ==, !=. By the end of this lesson you'll be able to compare numbers. Note that since we don't have a boolean type, we will stick with numbers and true expressions will result in 1.0 while false expressions will give us 0.0. Boolean types can be added in another extension/lesson.
'''
import traceback

# Forth source code
src = '2 3 <' # <1> 1.0 ok
# uncomment these other sources to try out more comparisons
# src = '1 2 ==' # <1> 0.0 ok
# src = '1 10 != 1 ==' # <1> 1.0 ok

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

# the size of the stack
STACK_CAPACITY = 1024
# generate STACK_CAPACITY values
stack = [Value() for _ in range(STACK_CAPACITY)]
# NOTE that the following will not give you what you want
# stack = [Value()] * STACK_CAPACITY
# this code will actually contain a list of the same instance of Value
# but the code above will create a unique instance for each entry
stack_top = -1

def tokenize(src):
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

def error_stack_underflow(word):
    raise XForthException(f'ERROR: {word} : Stack underflow')

# we'll use this to display what is currently on the stack
def stack_display():
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

# helper to check if a string is a number
def is_number(src):
    try:
        return float(src)
    except:
        return None

def interpret(tokens):
    # declare global access to stack_top
    global stack_top

    # iterate through each token
    for token in tokens:
        # numbers
        if number := is_number(token):
            # increment stack top
            stack_top += 1 
            # set the type to number
            stack[stack_top].type = ValueType.Number
            # assign the value
            stack[stack_top].value = number
        # operators
        elif token in OPERATORS:
            
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
            # note that we want to convert the bool value to a float 0.0 or 1.0
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
        else:
            raise XForthException(f'ERROR: Undefined token {token}')

if __name__ == '__main__':
    tokens = tokenize(src)
    print(f'** TOKENS **\n{tokens}')

    print(f'\n** INTERPRET **')
    try:
        interpret(tokens)
        stack_display()
    except XForthException as e:
        print(e)
    except:
        print('**DEV ERROR**') 
        traceback.print_exc()
