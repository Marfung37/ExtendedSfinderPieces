# imports
from sys import argv
from itertools import product, permutations
import re
import numpy as np

# get the pieces from the normal sfinder format
def getQueues(sfinderFormatPieces):
    '''use regex to match the notation'''

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



if __name__ == "__main__":
    # import time

    # start = time.time()
    # for i in range(100_000):
    #     
    # print(time.time() - start)
    x = getQueues("[TTSZ]p3")
    for a in x:
        print(a)
        
