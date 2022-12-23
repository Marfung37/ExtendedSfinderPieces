# ExtendedSfinderPieces
Extends the notation for sfinder pieces and output all the queues  
The queues are sorted with `TILJSZO` ordering

## Format
```python3 pieces.py [pieces...]```

## General Pieces Format
```pieces{modifier}```  
The modifier applies to the pieces  
To separate parts to be modify and not, delimitate with commas  
  
Ex: `SZ,Z*p2{modifier}`  
The modifier will apply to only the Z\*p2  

## Sfinder Pieces
The `[]` in the sfinder pieces are able to handle duplicate pieces

Ex: `[SSZ]!` any permutation of the pieces SSZ

## Modifiers
To apply multiple modifiers, use the `&&` and `||` operators. Use parentheses for grouping in the boolean expression.  
  
Ex: `pieces{modifier1 && (modifier2 || modifier3)}`

### Regex Modifier
Apply regular expression on the queues  
Prefix with a `!` for a not of the regex
  
Ex1: `pieces{/^[^L]{3}/}` no L in the first 3 pieces  
Ex2: `pieces{!/^T/}` doesn't start with a T

### Count Modifier
Apply a count of pieces on the queue   

Ex1: `pieces{T=1}` one T piece
Ex2: `pieces{LJ=2}` two of both L and J

Support operators: `=` or `==`, `!=`, `<`, `>`, `<=`, and `>=` 
  
### Before Modifier
Apply ordering of pieces in the queue  
Also matches if all before pieces exist in the queue

Ex1: `pieces{S < Z}` S piece is before Z  
Ex2: `pieces{LLJ < SI}`  All LLJ pieces exists before a S or I
