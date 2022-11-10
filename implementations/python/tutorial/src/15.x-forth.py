'''
Part 15 is quite short but really cool as we'll be implementing includes! We'll be able to include x-forth .xf files similar to C. We'll implement a single word 

include (compile-time-string -- ?) - includes the x-forth file at the given path only once

include is more like a keyword than a normal word because it is actually executed between tokenization and interpretation. Its string argument must be known at compile time
'''
import traceback
import sys
import os

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
    src = '"./include_me.xf" include a b + .'
    # output
    # this is just debug stuff, not actually part of normal x-forth output
    # EXPANDING INCLUDE ./include_me.xf...
    # EXPANDING TOKENS FOR /Volumes/Phill_Backup/pers/programming/x-forth/implementations/python/tutorial/src/include_me.xf
    # EXPANDING INCLUDE include_another.xf...
    # EXPANDING TOKENS FOR /Volumes/Phill_Backup/pers/programming/x-forth/implementations/python/tutorial/src/include_another.xf
    # EXPANDING INCLUDE include_another.xf...
    # EXPANDING INCLUDE ../src/include_another.xf...

    # 15.0




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
    Bool = auto()
    Address = auto()
    # our new string type
    String = auto()

# we'll use a dataclass for the value. We could (maybe should) just use tuples, but it will be nice to have named fields
from dataclasses import dataclass
from typing import Any

# X-Forth Constants
# we'll also create a constant for the value Undefined which is both the type and the constant
# the value will just be the hash of Undefined:
UNDEFINED = hash('Undefined:')    
# we can use these instead of the numbers themselves to avoid confusion
TRUE = 0.0
FALSE = 1.0

@dataclass
class Value:
    type: ValueType = ValueType.Undefined
    # note we'll now use UNDEFINED instead of None
    value: Any = UNDEFINED
    # is the value a constant?
    constant: bool = False
    # is the value a builtin value?
    # we can use this to filter the variables we show to only include user defined variables
    builtin: bool = False

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
    'type': lambda: stack_get_type(),
    'to-bool': lambda: to_bool(),
    'to-number': lambda: to_number(),
    # let's prefix our builtins with builtin_
    'length': lambda: builtin_length(),
    'append': lambda: builtin_append(),
    'to-string': lambda: builtin_to_string(),
    'symbol-from-string': lambda: builtin_symbol_from_string(),
}

# we'll also combine the operators and function like words into a single list for easy lookup
WORDS = [
    *OPERATORS,
    # note that we spread only the keys from FUNC_TABLE
    *FUNC_TABLE.keys()
]

# These are words and symbols which cannot be redefined
RESERVED_WORDS = [
    *[ o + ':' for o in OPERATORS],
    *[ f + ':' for f in FUNC_TABLE.keys()],
    *[ t.name + ':' for t in ValueType ],
    'True:',
    'False:',
    'include:',
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


# a place to store variables
# its a map of variable name symbol hashes to their Value
variables = dict()

# here we'll cache paths so we don't include them more than once
included_paths = []

# let's create a global table of symbols to avoid recreating them over and over
# it will be a table of hashes to symbol words so we can easily look up the word based on its hash
symbols = {
    # first we'll add our constants,
    hash('Undefined:') : 'Undefined:',
    hash('True:') : 'True:',
    hash('False:') : 'False:',
    # Adding entries for each of the ValueTypes in the form: 'Type:' : hash('Type:')
    **{ hash(sym) : sym for sym in [ t.name + ':' for t in ValueType ]},
}

# a bit of extra documentation
# adding the Tuple annotation 
from typing import List, Tuple

# this function prints the vars with their name instead of hash value
# we'll expand on this in a later lesson before exposing this function to X-Forth as the word 'variables'
from pprint import pprint
def pretty_vars():
    print('\n** VARIABLES **\n')
    # note that we don't print builtins
    pprint({symbols[k][:-1]: v for k,v in variables.items() if not v.builtin}, width=1)

# we're adding a location to the tokenize function
def tokenize(src: str, location: str) -> List[str]:
    '''tokenize breaks up a source string into a series of tokens, represented as a list of strings'''
    # remove leading and trailing whitespace
    src = src.strip()
    # the list of tokens to return
    # in X-B a token is just a string and thus tokens is a list of strings
    tokens = []
    # we will use this to build up tokens comprised of more than one char
    token = ''

    # first we'll change this to a while loop in order to gain more control over the loop
    index = 0
    while index < len(src):
    # for index, char in enumerate(src):
        # here we'll manually get the char
        char = src[index]
        # if we get a space we want to end the last token and add it to the token list
        if char.isspace():
            # only add the token if it isn't empty
            if token != '':
                # add the token to the list
                tokens.append(token)
            # reset the token to an empty string
            token = ''
        # x-forth strings begin with " (double quote)
        elif char == '"':
            # here we'll add the token if it is not empty
            # this allows things like 10"hello" to be parsed correctly
            if token != '':
                tokens.append(token)
                token = ''
            # string tokens start with "
            token += '"' 
            # move passed the first "
            index += 1
            # get the next char
            c = src[index]
            # get everything until we find another "
            # Let's modify this while loop slightly
            # while c != '"':
            while True:
                # # if the last char wasn't a backspace and the current char is a " we should end the string
                if c == '"' and token[-1] != '\\':
                    break
                # we need to check if we reach the end of the file before finishing the string
                if index >= len(src) -1:
                    raise XForthException(f'{location}ERROR: Unterminated String, expected " to end string {token} but found end of file')

                # add the char to the token
                token += c
                # incrememnt the index
                index += 1
                # get the next char
                c = src[index]
            # add the ending "
            token += '"'

            # we need to replace escaped characters with their real versions
            token = token.replace('\\n', '\n') # newline
            token = token.replace('\\r', '\r') # carriage return
            token = token.replace('\\t', '\t') # tab
            token = token.replace('\\"', '"')  # double quote

            tokens.append(token)
            # reset the token
            token = ''
        else:
            # append the character to the token string
            token += char
            # if we are at the end of the src we should add the token to the list
            if index >= len(src)-1:
                tokens.append(token)
        # now we need to manually increment the index
        index += 1
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
                index  = type_i
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

# this is a helper for printing and display so we don't have to copy and paste back and forth between stack_print and stack_display
def get_printed_value(value: ValueType) -> Any:
    '''get_printed_value takes a value and returns its printable form'''

    if value.type == ValueType.Symbol:
        return symbols[value.value]
    # bools
    elif value.type == ValueType.Bool:
        return 'True' if value.value == 0 else 'False'
    # undefined
    elif value.type == ValueType.Undefined:
        return 'Undefined'
    else:
        return value.value

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
            # get the printable value
            printed_value = get_printed_value(value)
            # for strings we want to include quotes for display
            if value.type == ValueType.String:
                # to display we don't want to actually print newlines instead want to escape them
                printed_value = printed_value.replace('\n', '\\n')
                printed_value = printed_value.replace('\r', '\\r') # also do carriage return for good measure
                printed_value = printed_value.replace('"', '\\"') # also we want quotes to be escaped
                # we want to display the string with leading and trailing quotes
                printed_value = '"' + printed_value + '"'
                # append the string token
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
    printed_value = get_printed_value(val)

    print(printed_value)

# TODO need to create a lookup table to cache absolute paths to avoid reimporting them in circular includes
# TODO make this function recursive
def builtin_expand_includes(tokens: List[str], show_info=False) -> List[str]:
    '''builtin_expand_includes includes external x-forth files.'''

    # we'll push the tokens to this list
    final_tokens = []

    # we need the index
    for i, token in enumerate(tokens):
        if token == 'include' and i > 0:
            if i < 1:
                raise XForthException(f'{location}ERROR: include : Expected literal string argument but found none')
            # get last token
            last_token = tokens[i-1]
            # check if it is a string
            if last_token.startswith('"') and last_token.endswith('"'):
                # have we included this path before?
                # default true
                path_included = True
                # exclude the quotes from the path
                xf_path = last_token[1:-1]
                # some info to show how often include is called
                if show_info:
                    # there should be a green version of this for each include
                    print(f'\x1b[92mEXPANDING INCLUDE {xf_path}...\x1b[0m')
                # if it is a .xf path
                if xf_path.endswith('.xf'):
                    if os.path.isfile(xf_path):
                        # convert to an absolute path
                        xf_path = os.path.abspath(xf_path)
                        if not xf_path in included_paths:
                            # info to show how often include actually reads and expands files
                            if show_info:
                                # there should be one yellow version for each file, even if multiple differing relative paths are used
                                # and even when it is included multiple times
                                print(f'\x1b[93mEXPANDING TOKENS FOR {xf_path}\x1b[0m')
                            # set path included to false
                            path_included = False
                            # open file and read source
                            with open(xf_path, 'r') as xf_file:
                                new_source = xf_file.read()
                    else:
                        raise XForthException(f'ERROR: {xf_path}: Source File Not Found')
                else:
                    raise XForthException(f'{location}ERROR: include : path {xf_path} is not a .xf file')

                # remove string path from final_tokens
                final_tokens.pop()
                
                # if we haven't included that path before
                if not path_included:
                    # cache path so we don't include more than once
                    included_paths.append(xf_path)
                    # get the tokens from the new_source
                    new_tokens = tokenize(new_source, xf_path)
                    # recursively expand includes
                    new_tokens = builtin_expand_includes(new_tokens, show_info)
                    # add the tokens to the final tokens
                    final_tokens.extend(new_tokens)

            # did not find expected string
            else:
                raise XForthException(f'{location}ERROR: include : Expected literal string argument but found token {last_token}')

        # append other tokens to final_tokens
        else:
            final_tokens.append(token)


    return final_tokens

# TODO load
# this needs to be above interpret because the interpreter needs to call it
# def builtin_load(tokens: List[str], once=True):
#     '''builtin_expand_includes includes external x-forth files.'''
#     global stack_top 

#     word = 'include' if once else 'load'
#     if stack_top < 0:
#         error_stack_underflow(word)

#     stack_invalid_types([ValueType.String], word=word)

#     # get value
#     v = stack[stack_top]
#     stack_top -= 1

#     # get path from the value
#     xf_path = v.value

#     if xf_path.endswith('.xf'):
#         if os.path.isfile(xf_path):
#             # convert to an absolute path
#             xf_path = os.path.abspath(xf_path)
#             with open(xf_path, 'r') as xf_file:
#                 new_source = xf_file.read()
#         else:
#             raise XForthException(f'ERROR: {xf_path}: Source File Not Found')
#     else:
#         raise XForthException(f'{location}ERROR: {word} : path {xf_path} is not a .xf file')

#     print(f'*** INCLUDE SOURCE {xf_path} ***')
#     print(new_source)



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
                        result = TRUE if a.value < b.value else FALSE
                    elif token == '>':
                        stack_invalid_types([ValueType.Number, ValueType.Number], top=stack_top+2, word=token)
                        result = TRUE if a.value > b.value else FALSE
                    # we don't check invalid stack for equality because you should be able to compare any types for equality
                    elif token == '==':
                        result = TRUE if a.value == b.value else FALSE
                    elif token == '!=':
                        result = TRUE if a.value != b.value else FALSE
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
            stack[stack_top].value = TRUE if token == 'True' else FALSE
        # var and con
        elif token == 'var' or token == 'con':
            # check for stack underflow
            # var needs at least 1
            if token == 'var' and stack_top < 0:
                error_stack_underflow(token)
            # con always needs 2
            if token == 'con' and stack_top < 1:
                error_stack_underflow(token)

            # validate that we have a value and a symbol
            # note that we don't want an exception raised because we need to check for vars overload
            value_symbol_sig = stack_invalid_types([ValueType.Any, ValueType.Symbol], raise_exception=False,word=token)
            symbol_sig = stack_invalid_types([ValueType.Symbol], raise_exception=False,word=token)
            # default value to Undefined
            value = UNDEFINED
            # check which signature we've found
            if value_symbol_sig == ():
                # get the value
                value = stack[stack_top]
                stack_top -= 1
            elif symbol_sig == ():
                # con requires a value
                if token == 'con':
                    #raise XForthException(f'{location}ERROR: con : Invalid Stack, expected a value of any type  at 0 and Symbol: at 1 but found {found} at {i}')
                    raise XForthException(f'{location}ERROR: con : Invalid Stack, expected a value of any type  at 0 and Symbol: at 1 but found only a Symbol: at 0, constants must be initialized with a value')
            # there was no valid sig
            else:
                _, found, i = value_symbol_sig if value_symbol_sig != () else symbol_sig
                if token == 'var':
                    msg = f'{location}ERRROR: var : Invalid Stack, expected either any value at 0 and Symbol: at 1 or a Symbol: at 0 but found {found} at {i}'
                else:
                    msg = f'{location}ERRROR: con : Invalid Stack, expected either any value at 0 and Symbol: at 1 but found {found} at {i}'
                raise XForthException(msg)

            # get the symbol
            symbol = stack[stack_top]
            # cannot redeclare constant that alread exists
            if symbol.value in variables.keys() and token == 'con':
                raise XForthException(f'{location}ERROR: con: Constant Redefinition, you cannot redeclare constant {symbols[symbol.value][:-1]}')
            # you also cannot redeclare anything in RESERVED_WORDS
            elif symbols[symbol.value] in RESERVED_WORDS:
                raise XForthException(f'{location}ERROR: Constant Redefinition, you cannot redeclare constant {symbols[symbol.value][:-1]}')
            # decrement stack
            stack_top -= 1
            
            # save the variable
            v = Value()
            # assign the value if it exists
            if value != UNDEFINED:
                v.type = value.type
                v.value = value.value
            # set the value as constant if we found con
            if token == 'con':
                v.constant = True
            # save the variable using its symbol's hash
            variables[symbol.value] = v
        # if is a defined variable
        # note we check the hash of the token + ':' to get its symbol name
        elif (var_hash := hash(token+':')) in variables.keys():
             # increment stack top
            stack_top += 1 

            # get variable
            v = variables[var_hash]
            # if constant push the value
            if v.constant:
            # if not constant push the address
                # set the type to Address
                stack[stack_top].type = v.type
                # assign the variables hash value
                stack[stack_top].value = v.value
            else:
                # set the type to Address
                stack[stack_top].type = ValueType.Address
                # assign the variables hash value
                stack[stack_top].value = var_hash
        # Undefined is simple
        elif token == 'Undefined':
            # increment stack top
            stack_top += 1 
            # set the type to Udnefined
            stack[stack_top].type = ValueType.Undefined
            # assign the value UNDEFINED
            stack[stack_top].value = UNDEFINED
         # read
        elif token == '!':
            # ! requires two arguments
            if stack_top < 1:
                error_stack_underflow('!')
            
            stack_invalid_types([ValueType.Any, ValueType.Address], word=token)

            # get value
            value = stack[stack_top]
            stack_top -= 1

            # get address
            addr = stack[stack_top]
            stack_top -= 1

            # write the type and value
            variables[addr.value].type = value.type
            variables[addr.value].value = value.value

        # # write
        elif token == '@':
            # ! requires one argument
            if stack_top < 0:
                error_stack_underflow('@')
            
            stack_invalid_types([ValueType.Address], word=token)

            # get address
            addr = stack[stack_top]
            # don't modify stack top since we'll be pushing again anyway
            # stack_top -= 1
            # stack_top += 1
            # get value
            value = variables[addr.value]

            # write the type and value to the stack
            stack[stack_top].type = value.type
            stack[stack_top].value = value.value
        # strings
        elif token.startswith('"') and token.endswith('"'):
            # increment stack top
            stack_top += 1 
            # set the type to string
            stack[stack_top].type = ValueType.String
            # assign the string without its leading and trailing "
            stack[stack_top].value = token[1:-1]
        # unkown token
        else:
            # suggest what the dev might have meant
            suggestion = ''
            # we'll check if a symbol exists and suggest that to the user in case they meant to type it
            if token + ':' in symbols.values():
                suggestion = f', did you mean the Symbol {token+":"} ? If so you forgot the ending ":" (colon)'
            raise XForthException(f'{location}ERROR: Undefined token {token}{suggestion}')

# bool conversion
def to_bool():
    '''to_bool converts numbers to bools, if the type value is a bool it does nothing'''
    # require 1 argument
    if stack_top < 0:
        error_stack_underflow('to-bool')

    # if the top value is a number do nothing
    if stack[stack_top].type == ValueType.Bool:
        return
    # for now we'll only implement number -> bool
    number_to_bool = stack_invalid_types([ValueType.Number], raise_exception=False, word='to-bool')

    if number_to_bool == ():
        # get value
        value = stack[stack_top]
        # don't modify stack top since we'll push back after popping 
        stack[stack_top].type = ValueType.Bool
        stack[stack_top].value = 0.0 if value.value == 0 else 1.0
    # invalid types
    else:
        _, found, index = number_to_bool
        error_stack_invalid_types([ValueType.Bool, ValueType.Number], found, index, word='to-bool')

# val to number conversion
def to_number():
    '''to_number converts values to numbers, if the top value is a number it does nothing'''
    # require 1 argument
    if stack_top < 0:
        error_stack_underflow('to-number')

    # if the top value is a number do nothing
    if stack[stack_top].type == ValueType.Number:
        return
    # for now we'll only implement and bool -> number
    bool_to_number = stack_invalid_types([ValueType.Bool], raise_exception=False, word='to-number')

    if bool_to_number == ():
        # get value
        value = stack[stack_top]
        # don't modify stack top since we'll push back after popping 
        stack[stack_top].type = ValueType.Number
        stack[stack_top].value = value.value 
    # invalid types
    else:
        _, found, index = bool_to_number
        error_stack_invalid_types([ValueType.Number, ValueType.Bool], found, index, word='to-number')

def builtin_length():
    '''builtin_length pushes the length of the top value on the stack which must be a string'''
    # require 1 argument
    if stack_top < 0:
        error_stack_underflow('length')

    # for now we'll only implement length for strings, but in a later lesson we'll be creating an overload for it
    string_length = stack_invalid_types([ValueType.String], raise_exception=False, word='length')

    if string_length == ():
        # get value
        value = stack[stack_top]
        # don't modify stack top since we'll push back after popping 
        stack[stack_top].type = ValueType.Number
        # push the length of the string as a float
        # note that we need to account for the unescaped string
        stack[stack_top].value = float(len(value.value))
    # invalid types
    else:
        _, found, index = string_length
        error_stack_invalid_types([ValueType.String], found, index, word='length')

def builtin_append():
    '''builtin_length concatenates values and pushes the new value to the stack'''
    global stack_top
    # require 2 arguments
    if stack_top < 1:
        error_stack_underflow('append')

    # for now we'll only implement append for strings, but in a later lesson we'll be creating an overload for it
    string_append = stack_invalid_types([ValueType.String, ValueType.String], raise_exception=False, word='append')

    if string_append == ():
        # get values
        b = stack[stack_top]
        stack_top -= 1

        a = stack[stack_top]
        # don't modify stack top since we'll push back after popping 
        # create the appended string
        new_string = a.value + b.value
        # push the appended string
        stack[stack_top].value = new_string
    # invalid types
    else:
        _, found, index = string_append
        error_stack_invalid_types([ValueType.String], found, index, word='append')


def builtin_to_string():
    '''builtin_to_string converts numbers and bools to strings'''
    if stack_top < 0:
        error_stack_underflow('to-string')

    # if the top value is a string do nothing
    if stack[stack_top].type == ValueType.String:
        return

    # number -> string and bool -> string
    number_to_string = stack_invalid_types([ValueType.Number], raise_exception=False, word='to-string')
    bool_to_string = stack_invalid_types([ValueType.Bool], raise_exception=False, word='to-string')
    symbol_to_string = stack_invalid_types([ValueType.Symbol], raise_exception=False, word='to-string')

    if bool_to_string == () or number_to_string == () or symbol_to_string == ():
        # get value
        value = stack[stack_top]
        # don't modify stack top since we'll push back after popping 
        string_value = UNDEFINED
        # number
        if value.type == ValueType.Number:
            string_value = str(value.value)
        elif value.type == ValueType.Symbol:
            string_value = symbols[value.value][:-1]
        # bool
        else:
            string_value = 'True' if value.value == TRUE else 'False'

        # set the type and value
        stack[stack_top].type = ValueType.String
        stack[stack_top].value = string_value
    # invalid types
    else:
        _, found, index = bool_to_string
        error_stack_invalid_types([ValueType.Number, ValueType.Bool], found, index, word='to-string')

def builtin_symbol_from_string():
    '''builtin_symbol_from_string converts a string into its symbol representation. Any string can be converted into a symbol even if the string does not end with ':'. So both `"Pig"` and `"Pig:"` convert to the symbol `Pig:`s'''
    # require 1 argument
    word = 'symbol-from-string'
    if stack_top < 0:
        error_stack_underflow(word)

    stack_invalid_types([ValueType.String], word=word)

    # get value
    v = stack[stack_top]
    # don't modify stack top since we'll push back after popping 
    # set the new value's type to symbol
    stack[stack_top].type = ValueType.Symbol
    # get the string from the value
    string = v.value
    # add the traling : if it does not exist
    if not string.endswith(':'):
        string = string + ':'

    # get the hash value
    hash_value = hash(string)
    # assign the new symbol to the symbols table
    symbols[hash_value] = string
    # push the symbol
    stack[stack_top].value = hash_value


if __name__ == '__main__':
    # now since tokenize can through an error we need to also put it in the try block
    try:
        tokens = tokenize(src, location)
        print(f'** TOKENS **\n{tokens}')

        # this version shows debug printing to show that a file is only ever included once 
        expanded = builtin_expand_includes(tokens, show_info=True)
        # using this version we expect to see 4 green includes but only 2 yellows
        # include appeared 4 times,  the file include_another.xf  was passed to include 3 times only actually included once
        # we'll use this version later on without the debug info shown
        #expanded = builtin_expand_includes(tokens)

        print(f'** INCLUDE EXPANDED TOKENS **\n{expanded}')


        print(f'\n** INTERPRET **')
        # pass the expanded tokens now
        interpret(expanded)
        # removing pretty_vars for now
        pretty_vars()
    except XForthException as e:
        print(e)
    except:
        print('**DEV ERROR**') 
        traceback.print_exc()
