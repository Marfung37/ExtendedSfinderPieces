# imports
from sys import argv
from itertools import product, permutations
import re
import numpy as np

# get the pieces from the normal sfinder format
def getQueues(sfinderFormatPieces):
    '''Get the pieces from the normal sfinder format'''

    BAG = "TILJSZO"
    pieceVal = {
        "T": "1",
        "I": "2",
        "L": "3",
        "J": "4",
        "S": "5",
        "Z": "6",
        "O": "7"
    }

    # two sections with prefix of pieces and suffix of permutate
    prefixPattern = "([*TILJSZO]|\[\^?[TILJSZO]+\])"
    suffixPattern = "(p[1-7]|!)?"
    
    # regex find all the parts
    sfinderFormatPiecesParts = re.findall(prefixPattern + suffixPattern, sfinderFormatPieces)
   
    # generate the queues
    queues = []
    for piecesFormat, permutateFormat in sfinderFormatPiecesParts:
        # generate the actual pieces
        # just a wildcard or a piece
        if len(piecesFormat) == 1:
            actualPieces = piecesFormat if piecesFormat != "*" else BAG
        # is a set of pieces
        else:
            actualPieces = re.match("\[\^?([TILJSZO]+)\]", piecesFormat).group(1)

            if piecesFormat[1] == "^":
                actualPieces = "".join(set(BAG) - set(actualPieces))
            
        # actual pieces is generated

        # determine the permutate for the pieces
        if permutateFormat:
            # ! ending meaning permutation of the pieces
            if permutateFormat == "!":
                queues.append(set(map("".join, permutations(actualPieces))))
            # some p\d ending
            else:
                # get the number at the end after p
                permutateNum = int(permutateFormat[-1])

                # as long as the number is at most the length of the pieces
                if permutateNum <= len(actualPieces):
                    queues.append(set(map("".join, permutations(actualPieces, permutateNum))))
                else:
                    # error
                    raise RuntimeError(f"{sfinderFormatPieces} has {piecesFormat + permutateFormat}"
                                       f" even though {piecesFormat} has length {len(actualPieces)}")
        else:
            # 1 piece queues
            queues.append(set(actualPieces))
    
    # do the product of each part for one long queue
    queues = sorted(map("".join, product(*queues)), key=lambda x: int(''.join((pieceVal[char] for char in x))))
    
    # return the generator object for the queues
    return queues

# make tree of the modifier to allow for easier parsing
def makeModifierTree(modifier, index=0, depth=0):
    '''Make tree of the modifier'''
    # holds the tree
    modifierTree = []

    # string to hold the current string before appending to tree
    currModifierString = ""

    # run through each character of the modifier
    while index < len(modifier):
        # get the character at that index
        char = modifier[index]

        # check if the char is the start of a regex expression
        if char == "/":
            # current string should be empty after a boolean operator unless it's a !
            if currModifierString != "!":
                raise RuntimeError(f"Unable to parse text before opening regex '{currModifierString}/'")

            try:
                # get the index of closing regex /
                closingSlashIndex = modifier.index("/", index + 1)
                
                # get the text in the regex and add it to the tree along with if there's a !
                modifierTree.append(currModifierString + modifier[index: closingSlashIndex + 1])
                currModifierString = ""

                # move index to end of the regex
                index += closingSlashIndex + 1

            # the closing slash wasn't found
            except ValueError:
                raise RuntimeError(f"No closing slash for regex at '{modifier[index:]}'")

        # opening parentheses
        elif char == "(":
            # current string should be empty after a boolean operator
            if currModifierString:
                raise RuntimeError(f"Unable to parse text before opening parentheses '{currModifierString}('")

            # handle the subtree with recursion
            subTree, i = makeModifierTree(modifier, index + 1, depth + 1)

            # add the sub tree to the tree
            modifierTree.append(subTree)

            # move index to the end of the parentheses section
            index = i

        # closing parentheses
        elif char == ")":
            # if on a sub tree
            if depth != 0:
                # add the current string to the subtree
                if currModifierString:
                    modifierTree.append(currModifierString)

                # return the sub tree
                return modifierTree, index
            # on the main tree and error
            else:
                raise RuntimeError(f"Missing opening parentheses with '{modifier[: index + 1]}'")
        
        # boolean operator
        elif char == "&" or char == "|":
            # append the current string to tree
            modifierTree.append(currModifierString)
            currModifierString = ""

            # if there's two & or |
            if modifier[index + 1] == char:
                # append the operator the tree
                modifierTree.append(char * 2)
                index += 1
            # there's only one & or |
            else:
                raise RuntimeError(f"Missing second character of '{char}'")
        
        # some other character
        else:
            currModifierString += char
        
        # increment the index
        index += 1
    
    # append the final current string if on the main tree
    if depth == 0:
        if currModifierString:
            modifierTree.append(currModifierString)
    # on a sub tree meaning no closing parentheses
    else:
        raise RuntimeError(f"Missing closing parentheses")
    
    # return the main tree
    return modifierTree

# check if a queue is allowed by the modifier
def checkModifier(queue, modifier):
    '''Check if a queue is allowed by the modifier'''
    pass


# handle the whole extended sfinder pieces
def main(extendedSfinderFormatPieces):
    '''Handle the whole extended sfinder pieces'''

    # split by comma
    extendedSfinderPiecesParts = extendedSfinderFormatPieces.split(",")

    # for each part get the pieces and modifier
    for part in extendedSfinderPiecesParts:
        # get a match obj with regex for the pieces and modifier
        matchWithModifier = re.match("^(.+){(.+)}$", part)

        # check if there was in fact a modifier to match
        if matchWithModifier:
            # get the pieces and modifier
            sfinderFormatPieces, modifier = matchWithModifier.groups()
        else:
            # get the pieces and set modifier to None
            sfinderFormatPieces, modifier = extendedSfinderPiecesParts, None
        
        # get the queues
        queues = getQueues(sfinderFormatPieces)

        # apply modifier
        for queue in queues:
            pass


if __name__ == "__main__":
    # import time

    # start = time.time()
    # for i in range(100_000):
    #     
    # print(time.time() - start)

    print(makeModifierTree("(SZ||!/S/"))
        
