# ExtendedSfinderPieces
Extends the notation for sfinder pieces and output all the queues  
The queues are sorted with `TILJSZO` ordering

## Format
```python3 pieces.py "[pieces...]"```
Quote the pieces arguments due to cli reading some symbols like `{}`, `*`, `!`, `;`, `&&`, etc. as operators in a command  

## General Pieces Format
```pieces{modifier}```  
The modifier applies to the pieces  
To separate parts to be modify and not, delimitate with commas  
Parentheses are supported for applying a modifier on pieces already modified  
Use semicolons to add different extended sfinder pieces into same list  
  
Ex1: `SZ,Z*p2{modifier}` The modifier will apply to only the Z\*p2  
Ex2: `(SZ,Z*p2){modifier}` The modifier will apply to SZ,Z*p2  
Ex3: `pieces1{modifier1};pieces2{modifier2}` Using semicolons  

## Sfinder Pieces
The `[]` in the sfinder pieces are able to handle duplicate pieces  

Ex: `[SSZ]!` any permutation of the pieces SSZ

## Modifiers
Boolean expression operators, `&&`, `||`, and `!` are supported. Use parentheses to change order from left to right.  
The prefix with format `<index>-[index]:` can apply to modifiers to modify a substring of the queue. Only putting one number works as left # pieces in the queue.   
  
Ex1: `pieces{modifier1 && (modifier2 || modifier3)}`  
Ex2: `pieces{1-2:modifier1 && 2:(modifier2 && modifier3)}`  
Different ways to use the prefix: 1-2 is the 2nd character and 2 is the left 2 characters  

### Regex Modifier
Apply regular expression on the queues   
  
Ex1: `pieces{/^[^L]{3}/}` no L in the first 3 pieces  
Ex2: `pieces{!/^T/}` doesn't start with a T  

### Count Modifier
Apply a count of pieces on the queue   

Ex1: `pieces{T=1}` one T piece  
Ex2: `pieces{LJ=2}` two of both L and J  
Ex3: `pieces{[LJ]=1}` one of L or J  
Ex4: `pieces{LS[IZ]=1}` one of each L and S and one of I or Z  
Ex5: `pieces{[*]=2}` wildcard character acts like TILJSZO. two of any character  

Supported operators: `=` or `==`, `!=`, `<`, `>`, `<=`, and `>=`  
  
### Before Modifier
Apply ordering of pieces in the queue  
Also matches if all before pieces exist in the queue
Set notation with `[]` is supported which represents or of the pieces    

Ex1: `pieces{S < Z}` S piece is before Z  
Ex2: `pieces{LLJ < SI}`  All LLJ pieces exists before a S or I  
Ex3: `pieces{S<[IL]Z}` S is before I or L and always before Z  
