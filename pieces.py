# imports
from sys import argv
from itertools import product, permutations, chain
from string import whitespace
import re

# sort queues
def sortQueues(queues):
    '''Sort the queue with TILJSZO ordering'''
    pieceVal = {
        "T": "1",
        "I": "2",
        "L": "3",
        "J": "4",
        "S": "5",
        "Z": "6",
        "O": "7"
    }

    return (q for q in sorted(queues, key=lambda x: int(''.join((pieceVal[char] for char in x)))))

# get the pieces from the normal sfinder format
def getQueues(sfinderFormatPieces, sortQueuesBool=True):
    '''Get the pieces from the normal sfinder format'''

    BAG = "TILJSZO"

    # two sections with prefix of pieces and suffix of permutate
    prefixPattern = "([*TILJSZO]|\[\^?[TILJSZO]+\])"
    suffixPattern = "(p[1-7]|!)?"
    
    # regex find all the parts
    sfinderFormatPiecesParts = re.findall(prefixPattern + suffixPattern, sfinderFormatPieces)

    # check if there wasn't a mistake in the finding of parts
    if ''.join(map(''.join, sfinderFormatPiecesParts)) != sfinderFormatPieces:
        # doesn't match
        raise RuntimeError("Bad input for sfinder format pieces")
   
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
    queues = map("".join, product(*queues))

    # sort the queues
    if sortQueuesBool:
        queues = sortQueues(queues)
    
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
            if currModifierString != "!" and currModifierString != "":
                raise RuntimeError(f"Unable to parse text before opening regex '{currModifierString}/'")

            try:
                # get the index of closing regex /
                closingSlashIndex = modifier.index("/", index + 1)
                
                # get the text in the regex and add it to the tree along with if there's a !
                modifierTree.append(currModifierString + modifier[index: closingSlashIndex + 1])
                currModifierString = ""

                # move index to end of the regex
                index = closingSlashIndex

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
            # ignore whitespace
            if char not in whitespace:
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

# handle operator in the modifier
def handleOperatorInModifier(currBool, newBool, operator, modifierType):
    '''Handle the operator in the modifier'''

    # and operator
    if operator == "&&":
        return currBool and newBool
    # or operator
    elif operator == "||":
        return currBool or newBool
    else:
        # something went wrong
        errorPrefix = "Something went wrong when parsing leading to not catching no operator before a "
        raise RuntimeError(errorPrefix + modifierType)

# handle the different operators for the count modifier
def handleCountModifier(countPieces, queue, relationalOperator, num):
    '''Handle the different operators for count modifier'''

    # check each piece
    for piece in countPieces:
        # count the number of occurrences of that piece
        pieceCount = queue.count(piece)

        # handle all the possible operators
        if relationalOperator == "=" or relationalOperator == "==":
            if pieceCount != num:
                return False
        elif relationalOperator == "!=":
            if pieceCount == num:
                return False
        elif relationalOperator == "<":
            if pieceCount >= num:
                return False
        elif relationalOperator == ">":
            if pieceCount <= num:
                return False
        elif relationalOperator == "<=":
            if pieceCount > num:
                return False
        elif relationalOperator == ">=":
            if pieceCount < num:
                return False
    
    return True

# handle the before operator
def handleBeforeOperator(beforePieces, afterPieces, queue):
    '''Handle the before operator'''
    beforePieces = list(beforePieces)

    # tries to match all the pieces in beforePieces before seeing any of the after pieces
    for piece in queue:
        # check if it's an after piece
        if piece in afterPieces:
            # hit a after piece before getting through all the before pieces
            return False
        # check if it's a before piece
        elif piece in beforePieces:
            # remove this piece from the before pieces
            beforePieces.remove(piece)

            # if beforePieces is empty
            if not beforePieces:
                return True
    
    # if gone through the whole queue and still not sure, then assume False
    return False

# check if a queue is allowed by the modifier
def checkModifier(queue, modifierTree):
    '''Check if a queue is allowed by the modifier'''
    # holds the current boolean as parse through the modifier tree
    currBool = True

    # operator starts with and
    operator = "&&"

    # for each modifier part in the tree
    for modifierPart in modifierTree:
        if isinstance(modifierPart, list):
            # get the boolean from the submodifier
            subModifierCheck = checkModifier(queue, modifierPart)

            # get new current boolean
            currBool = handleOperatorInModifier(currBool, subModifierCheck, operator, "sub modifier")

            # if currBool is False and the rest of the tree are and (which should be common), then return False directly
            if not currBool:
                # try to find any or operators
                if "||" not in modifierTree:
                    # don't find any other '||', therefore all ands or near the end and can simply return False
                    return False
           
            # clear the operator
            operator = ""
        
        # handle the modifiers
        elif isinstance(modifierPart, str):
            # count modifier 
            if countModifierMatchObj := re.match("^([TILJSZO]+)([<>]|[<>=!]?=)(\d+)$", modifierPart):
                # get the different sections of the count modifier
                countPieces, relationalOperator, num = countModifierMatchObj.groups()

                # get the boolean for the count modifier
                countBool = handleCountModifier(countPieces, queue, relationalOperator, int(num))

                # get new current boolean
                currBool = handleOperatorInModifier(currBool, countBool, operator, "count modifier")

                # if currBool is False and the rest of the tree are and (which should be common), then return False directly
                if not currBool:
                    # try to find any or operators
                    if "||" not in modifierTree:
                        # don't find any other '||', therefore all ands or near the end and can simply return False
                        return False

                # clear the operator
                operator = ""
            
            # before modifier
            elif beforeModifierMatchObj := re.match("^([TILJSZO]+)<([TILJSZO]+)$", modifierPart):
                # get the before and after pieces
                beforePieces, afterPieces = beforeModifierMatchObj.groups()

                # get the boolean for if the queue does match the before modifier
                beforeBool = handleBeforeOperator(beforePieces, afterPieces, queue)

                # get new current boolean
                currBool = handleOperatorInModifier(currBool, beforeBool, operator, "before modifier")

                # if currBool is False and the rest of the tree are and (which should be common), then return False directly
                if not currBool:
                    # try to find any or operators
                    if "||" not in modifierTree:
                        # don't find any other '||', therefore all ands or near the end and can simply return False
                        return False
                
                # clear the operator
                operator = ""

            # regex modifier
            elif regexModifierMatchObj := re.match("(!?)/(.+)/", modifierPart):
                # get the negate and regex pattern
                negate, regexPattern = regexModifierMatchObj.groups()

                # get the boolean for if the queue matches the regex pattern
                regexBool = bool(re.match(regexPattern, queue))
                if negate == "!":
                    regexBool = not regexBool

                # get new current boolean
                currBool = handleOperatorInModifier(currBool, regexBool, operator, "regex modifier")

                # if currBool is False and the rest of the tree are and (which should be common), then return False directly
                if not currBool:
                    # try to find any or operators
                    if "||" not in modifierTree:
                        # don't find any other '||', therefore all ands or near the end and can simply return False
                        return False
                
                # clear the operator
                operator = ""

            # handle operator
            elif modifierPart == "&&" or modifierPart == "||":
                operator = modifierPart

            else:
                # something went wrong
                raise RuntimeError("Something went wrong when parsing leading to no match to modifiers or operator")
        
        else:
            # something went wrong
            raise RuntimeError("Something went wrong leading to some modifier that isn't a string or list in the modifier tree")

    # return the boolean
    return currBool

# handle the whole extended sfinder pieces
def handleExtendedSfinderFormatPieces(extendedSfinderFormatPieces, sortQueuesBool=True):
    '''Handle the whole extended sfinder pieces'''

    # split by comma
    extendedSfinderPiecesCommaSplit = extendedSfinderFormatPieces.split(",")


    # split by if there's a closing bracket
    extendedSfinderPiecesParts = []
    for part in extendedSfinderPiecesCommaSplit:
        # split the part
        splitedPart = re.split("(.+?{.*})", part)

        # remove empty strings and extend to rest of the parts
        extendedSfinderPiecesParts.extend(filter(None, splitedPart))

    # holds the entire queues
    queues = []

    # for each part get the pieces and modifier
    for part in extendedSfinderPiecesParts:
        # get a match obj with regex for the pieces and modifier
        matchWithModifier = re.match("^(.+){(.*)}$", part)

        # check if there was in fact a modifier to match
        if matchWithModifier:
            # get the pieces and modifier
            sfinderFormatPieces, modifier = matchWithModifier.groups()
        else:
            # get the pieces and set modifier to None
            sfinderFormatPieces, modifier = part, None
        
        # get the queues
        queuesPart = getQueues(sfinderFormatPieces, sortQueuesBool=False)

        # create the modifier tree if there is a modifier
        if modifier is not None:
            # make the modifier tree
            modifierTree = makeModifierTree(modifier)

            # filter the queues with the modifier tree
            queuesPart = filter(lambda x: checkModifier(x, modifierTree), queuesPart)
        
        # append this queues part into the list of queues
        queues.append(queuesPart)
    
    # do the product of each part for one long queue
    queues = map("".join, product(*queues))

    # sort the queues
    if sortQueuesBool:
        queues = sortQueues(queues)
        

    # return the queues as a generator object
    return queues

# handle user input and runs the program
def main(customInput=argv[1:], printOut=True):
    '''Main function for handling user input and program'''
    
    # get the user input
    userInput = customInput

    # spliting to get the extended sfinder format pieces
    allExtendedSfinderPieces = []
    for argument in userInput:
        allExtendedSfinderPieces.extend(re.split("\n|;", argument))

    # hold all the queues parts 
    queues = []

    # go through part of the user input that's a extended sfinder format pieces
    for extendedSfinderPieces in allExtendedSfinderPieces:
        # get the queues from this format
        queuesPart = handleExtendedSfinderFormatPieces(extendedSfinderPieces, sortQueuesBool=False)
        queues.append(queuesPart)

    # sort the queues
    queues = sortQueues(chain(*queues))
        
    if printOut:
        # print out the queues
        print("\n".join(queues))
    else:
        # return the queues generator obj
        return queues
        

if __name__ == "__main__":
    # run the main function
    main()
