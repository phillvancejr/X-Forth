'''
Part 8 will be short and simple since we've introduced a lot of the foundation for additional types. In X-Forth, 0.0 is treated as truthy or no error and 1.0 is treated as falsey or some error. This is odd compared to C but it does help to think in terms of errors rather than true or false: 0.0 means no error ocurred and 1.0 (or any other number) denotes that an error occured and which one. The values True and False are used to represent these values when printing or when used as literals
'''
import traceback
import sys
import os.path

# if an argument was passed to the file
if len(args := sys.argv[1:]) > 0:
    # get the argument
    filename = args[0]
    if filename.endswith('.forth'):
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
    src = 'some-symbol: type .' # Symbol:
    # uncomment below for some extra programs
    # src = '1 2 < .' # True
    # src = 'one: 2 < .' # ERROR: < : Invalid Stack, expected type(s): Number for stack value at position 1 but found Symbol
    # src = 'one: one: == .' # True
    # src = 'one: 1 == .' # False
    # src = 'True .' # True
    # src = 'True False == .' # False
    # src = '10 type Number: == . .s'
    # # output
    # # False
    # # <0> ok

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
    Symbol = auto()
    # This type is for internal use, allowing us to check against any value type
    Any = auto()
    # add a bool type
    Bool = auto()

# we'll use a dataclass for the value. We could (maybe should) just use tuples, but it will be nice to have named fields
from dataclasses import dataclass
from typing import Any

    
@dataclass
class Value:
    type: ValueType = ValueType.Undefined
    value: Any = None

# we're going to move the operators into sub lists to make it easier to check the stack arguments based on the type of operator
MATH_OPERATORS = [
    '+',
    '-',
    '*',
    '/',
]

LOGIC_OPERATORS = [
    '<',
    '>',
    '==',
    '!=',
]
# operators
OPERATORS = [
    # math
    *MATH_OPERATORS,
    # logic
    *LOGIC_OPERATORS,
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
    'show': lambda: stack_print(consume=False),
    # new word type to get the type of the value on the stack
    'type': lambda: stack_get_type()
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

# let's create a global table of symbols to avoid recreating them over and over
# it will be a table of hashes to symbol words so we can easily look up the word based on its hash
symbols = {
    # Adding entries for each of the ValueTypes in the form: 'Type:' : hash('Type:')
    **{ hash(sym) : sym for sym in [ t.name + ':' for t in ValueType ]}
}
# a bit of extra documentation
# adding the Tuple annotation 
from typing import List, Tuple

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

# error helper for invalid stack types
def error_stack_invalid_types(expected_types: List[ValueType], found_type: ValueType, index: int, word=None):
    '''This is raised when the stack desn't contain the expected types. Note that the word is an optional argument that can be used to give context on the word that errored'''
    expected_types = ' or '.join([ t.name for t in expected_types])
    word = word + ' : ' if word else ''
    raise XForthException(f'{location}ERROR: {word}Invalid Stack, expected type(s): {expected_types} for stack value at position {index} but found {found_type.name}')

# this function will help us to assert that the stack contains specific types
# Now that we have multiple types we need to assert that we have the required types for words
def stack_invalid_types(type_list: List[ValueType], raise_exception: bool = True, top: int = None, word=None) -> Tuple[ValueType, int, ValueType]:
    '''stack_invalid_types expects a list of one or more valid types. Each type represents the valid type for the current stack value.  If raise_exception is True then the function raises an exception detailing the invalid types, otherwise you get either an empty tuple, which signifies the stack is valid, or a tuple of values representing ( expected_type: ValueType, found_type: ValueType, current_stack_value_index: int ). 

    Parameters
        type_list - the list of types to check, using ValueType.Any will allow any value
        raise_exception - should an exception be raised if the stack is invalid?
        top - this is the index to start checking values at, it defaults to stack_top if none is passed
        word - optionally the word you're currently checking

    example, asserting that the top value is either a number the second value is a number and raising an exception if the assertion is false
    stack_invalid_types(
        ValueType.Number, # top value
        ValueType.Number # second value
     )
    '''
    # top should default to the stack top if non is passed
    top = top if top else stack_top
    # get the number of values to check
    value_count = len(type_list)
    # we need a separate counter to iterate through the type_list
    type_i = 0
    # loop backwards through the stack, top to bottom
    for i in range(top, top - value_count,-1):
        # get the value to check
        value = stack[i]
        # get the valid_type
        valid_type = type_list[type_i]
        # loop through valid types to check if the value's type is included
        if value.type != valid_type and valid_type != ValueType.Any:
            if raise_exception:
                # this calculates the index such that the top stack value is 0, the next is 1, etc
                index = value_count - type_i
                error_stack_invalid_types([valid_type], value.type, index, word)
                # raise XForthException(f'{location}ERROR: Invalid Stack, expected type(s): {valid_type} for stack value at index {i} but found {value.type.name}')
            return (valid_type, value.type, i)
        # increment type_i
        type_i += 1
    return ()

# copy and pasted stack_print for simplicity
def stack_get_type():
    '''stack_get_type pushes the type of the top value as as symbol. If the type is Number then Number: is pushed
    errors:
        Stack underflow'''
    global stack_top
    # print requires 1 argument so the stack_top must be >= 0
    if stack_top < 0:
        # if there aren't enough arguments that is a stack underflow
        error_stack_underflow('type')
    # get the value from the top of the stack
    val = stack[stack_top]
    # get the vals type name and convert it to a hash
    type_symbol_hash = hash(val.type.name+':')
    # we don't increment the stack because we're replacing the current value with its type
    # set the new value's type to a symbol
    stack[stack_top].type = ValueType.Symbol
    # get the symbol created from the type's name
    stack[stack_top].value = type_symbol_hash

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
            # similar to stack_print we need to take the type into consideration now
            printed_value = None
            # symbols
            if value.type == ValueType.Symbol:
                printed_value = symbols[value.value]
            # bools
            elif value.type == ValueType.Bool:
                printed_value = 'True' if value.value == 0 else 'False'
            else:
                printed_value = value.value
            print(f'{printed_value} ', end='')

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
    # Since we've introduce a new type we now need to check the type since different types may have different values
    if val.type == ValueType.Symbol:
        print(symbols[val.value])        
    # bools
    elif val.type == ValueType.Bool:
        print('True' if val.value == 0 else 'False')
    else:
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
                # we'll now assign the type since we have multiple types words can operate on
                result_type = ValueType.Undefined
                # perform the correct operation based on the operator
                # math operators
                if token in MATH_OPERATORS:
                    # for now all math operators require both arguments to be numbers
                    # note that we pass stack_top+2 as the top becaues we've already popped the two arguments off the stack
                    stack_invalid_types([ValueType.Number, ValueType.Number], top=stack_top+2, word=token)
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
                    result_type = ValueType.Number
                if token in LOGIC_OPERATORS:
                    # boolean operators
                    # note that we want to convert the bool value to a float 1.0 or 0.0
                    # < and > only operate on numbers
                    # Here will will start using True and False instead of 0 and 1
                    if token == '<':
                        stack_invalid_types([ValueType.Number, ValueType.Number], top=stack_top+2, word=token)
                        result = 0.0 if a.value < b.value else 1.0
                    elif token == '>':
                        stack_invalid_types([ValueType.Number, ValueType.Number], top=stack_top+2, word=token)
                        result = 0.0 if a.value > b.value else 1.0
                    # we don't check invalid stack for equality because you should be able to compare any types for equality
                    elif token == '==':
                        result = 0.0 if a.value == b.value else 1.0
                    elif token == '!=':
                        result = 0.0 if a.value != b.value else 1.0
                    result_type = ValueType.Bool

            # push the value back onto the stack 
            # first increment stack_top
                stack_top += 1
                # assign the result to the value
                stack[stack_top].value = result
                # use the result_type value since it changes now
                stack[stack_top].type = result_type
            # function words
            else:
                # lookup and call the function from FUNC_TABLE
                FUNC_TABLE[token]()
        # symbols
        elif token.endswith(':'):
             # increment stack top
            stack_top += 1 
            # set the type
            stack[stack_top].type = ValueType.Symbol 
            # create the symbol hash
            symbol_hash = hash(token)
            # if its not in the symbols dict we should add it
            if not symbol_hash in symbols.keys():
                symbols[symbol_hash] = token
            # set the value to the hash of the symbol's token
            stack[stack_top].value = symbol_hash
        # bools
        elif token == 'True' or token == 'False':
            # increment stack top
            stack_top += 1 
            # set the type to bool
            stack[stack_top].type = ValueType.Bool
            # assign the value, note that we still use numeric values
            stack[stack_top].value = 0.0 if token == 'True' else 1.0

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
