'''
For the first tutorial we will tokenize (break up) the Forth source code into a list of strings
'''
# Forth source code
src = '2 3'

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

if __name__ == '__main__':
    tokens = tokenize(src)
    print(f'** TOKENS **\n{tokens}')