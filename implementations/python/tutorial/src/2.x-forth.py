'''
In part 2 we'll introduce the stack and begin the interpreter. Yes, we're already starting the interpreter. Unlike most languages, Forth source code does not need to be parsed into an Abstract Syntax Tree (AST) and can instead be directly executed.
'''
import traceback
# Forth source code
src = '2 3'

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
        else:
            raise XForthException(f'Undefined token {token}')

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
