# ExtendedSfinderPieces

A parser to generate Tetris queues based on
[sfinder](https://github.com/knewjade/solution-finder) notation for generating queues.
This project extends on this notation with several features,
mainly ability to filter the queues.

## Usage

As a CLI utility,

```sh
python3 pieces.py "[pattern]"
```

The quotes around the pattern helps prevents the shell from interpreting symbols
in the `pattern` as shell symbols such as `!`, `&`, `|`, or `^`.

## Format

A pattern (the string to be parsed) is built from two component types:

- **generator** - produces queues.  
Examples:
  - Tetrominos (`T`, `I`, `L`, ...)
  - All permutations of the 7 tetrominos (`*p7`)
- **filter** - applies a constraint to the queue built so far.  
Examples:
  - `{L<S}` filters for queues where L appears before S.

> **Note:** whitespace is ignored to allow for readability of patterns

A pattern is a sequence of these components:

```text
<generator>[{<filter>}] [<generator>[{<filter>}]]...
```

A pattern usually is one or more generators followed by a filter:

```text
*p7{L<S}  => ['TILJSZO', 'TILJSOZ', ...] # all perms, require L before S
TSZO{T<O} => ['TSZO']                    # the queue TSZO, require T before O
TSZO{O<T} => []                          # the queue TSZO, require O before T
```

However, a filter can follow *any* generator, where the filter applies only to
what has been generated so far.

```text
TSZ{S<Z}O{T<O} => ['TSZO'] # the queue TSZ, require S < Z, xO, require T < O
```

Generators combine by combining every possibility from one with every
possibility from the next (a Cartesian product).
For example, `*p7*p7` would have for each permutation of the tetrominos say `TILJSZO`
it is followed by another permutation of the tetrominos say `IJLSTOZ` to get
`TILJSZOIJLSTOZ` as a queue.

### Generator

A generator consists of two parts:

- **pool** - a collection of pieces to pull from
- **permute** - number of pieces to pull out of the pool

> **Note:** generator output is sorted following TILJSZO ordering

#### Pool

A pool in the most verbose form consist of pieces in braces

```text
[T]
[I]
[TILJSZO]
[TIL]
[IIL]
```

However, there are shorthand for common pools:
the tetrominos and the pool of all the pieces.

```text
# shorthand for TILJSZO tetrominos
T -> [T]
I -> [I]

# shorthand for pool of all pieces
* -> [TILJSZO]
```

The `^` modifier takes the set complement of the pool from the `*` pool.

```text
# complement of [T]: [TILJSZO] remove [T] -> [ILJSZO]
[^T]   -> [ILJSZO]
[^I]   -> [TLJSZO]

# complement of [TIJ]: [TILJSZO] remove [TIJ] -> [LSZO]
[^TIJ] -> [LSZO]
```

A pool can contain inner pools to create variations of the pool.
Each choice of the inner pool generates a separate combination for the pool.
A pool cannot be nested into inner pool as redundant behavior.

```text
# Inner pool [SZ] has 2 choices, creating 2 variations:
[TI[SZ]]     -> [TIS] or [TIZ]

# Two inner pools multiply together (2 choices * 2 choices = 4 variations)
[TI[LJ][SZ]] -> [TILS], [TILZ], [TIJS], or [TIJZ]

# ^ modifier only applies to current depth of pool
[^TI[SZ]]    -> [LJSZO[SZ]] -> [LJSSZO] or [LJSZZO]
[TI[^SZ]]    -> [TI[TILJO]] -> [TIT], [TII], [TIL], [TIJ], or [TIO]

# Error: can't nest pool inside a inner pool
[I[T[LJ]]]   -> Error 
```

Conceptually, `[I[T[LJ]]] = [I[TL]] or [I[TJ]] = [IT], [IL], [IT], or [IJ]`,
which is the same as `[I[TLJ]]`, so nesting pools more is does not provide
any more functionality as a flatten inner pool.

#### Permute

Each pool can be followed by the expression for **permute**
to denote the length of the permutations.
Exception for pools of the form of a tetromino, which cannot be followed
by any permute expression as one piece can only have one permutation of itself.

The **permute** expression consist of `p<permute>`

```text
# tetromino only permutation is itself
T          -> T

# permutations of TIL of size 3
[TIL]p3    -> TIL, TLI, ITL, ILT, LTI, LIT

# permutations of TIL of size 2
[TIL]p2    -> TI, TL, IL

# permutations of TI[SZ] of size 2
[TI[SZ]]p2 -> [TIS]p2 or [TIZ]p2 
           -> TI, TS, TZ, IT, IS, IZ, ST, SI, ZT, ZI

# permutations of all pieces of size 7
*p7        -> TILJSZO, TILJSOZ, TILJZSO, ...
```

In general, not including an **permute** expression is permuting with size of 1.

```text
T                   -> T
[TIL] -> [TIL]p1    -> T, I, L
*     -> [TLJSZO]p1 -> T, I, L, J, S, Z, O
```

A shorthand for all permutations of the size of the pool is `!`.
This is helpful to just get all permutations without
needing to know the size of the pool.

```text
[TIL]    -> [TIL]p3
[T[SZ]]  -> [T[SZ]]p2
*!       -> *p7
```

### Filter

The **filter** component consist of a boolean expression with operations:
`!` (NOT), `&&` (AND), and `||` (OR).
Moreover, parentheses `()` can denote the precedence in the boolean expression.

There are three types of propositions or literals:

- **count** - true if queue satisfies a certain count of the pieces
- **before** - true if queue satisfies a particular ordering of the pieces
- **regex** - true if the queue satisfies the regex expression

#### Count

The **count** literal has the form

```text
<pieces> <operation> <number>
```

The possible operations are `=`, `!=`, `<`, `>`, `<=`, and `>=`.

```text
T=1   # require exactly 1 T in the queue
T=0   # require exactly 0 T in the queue
TL!=0 # require both T and L show up in the queue
```

The `<pieces>` token can allow for wildcards and the `[]` notation for combinations.
Pieces outside of `[]` denote logical AND while pieces in `[]` are logical OR.

> **Note:** `<pieces>` is not the same as **pool**, but they are similar.
`<pieces>` support does not have `^` modifier or allow nesting for `[]`.

```text
*=1         -> TILJSZO=1
[SZ]=1      -> S=1 || Z=1
T[SZ]=1     -> TS=1 || TZ=1
T[LJ][SZ]=1 -> TLS=1 || TLZ=1 || TJS=1 || TJZ=1
[*]=2       -> T=2||I=2||L=2||J=2||S=2||Z=2||O=2
```

#### Before

The **before** literal has the form

```text
<before pieces> < <after pieces>
```

This uses the same `<pieces>` token described in the [count literal](#count).

```text
L<S     # L before S
LL<S    # 2 L's before S
T[LJ]<S # T before S and L or J before S
L<SZ    # L before both S and Z
L<[SZ]  # L before S or Z
L<SS    # L before 2 S's, equivalent to L<S
```

If "before piece" appears but a "after piece" does not appear in the queue,
the expression is evaluated to TRUE.
For example, `TILZ` satisfies `L<S` as L appears and S does not.

To understand why this is accepted as "before", consider

```text
[ISZO]!,*p3{L<S}
```

After the `*p3` are 4 more pieces to fill the 7 bag, if an L piece is
seen and an S is not seen then the L is before the S as its in the
following 4 pieces.
In general, this is the usual use case, and more intuitive
understanding in saying "L before S" with 7 bag.

Each distinct piece listed is based on the
first appearance of the piece in the queue.
For example, `SLS` does not satisfy `L<S`
as the first L is not before the first S.
For duplicate pieces, they correspond to the nth instance of the piece.
`SLS` does not satisfy `SS<L` as first S is before L but
the second S is not before the L.

#### Regex

The **regex** literal has the form

```text
/<regex>/
```

Or, in other words, the regex is within `/.../`.

```regex
/^I/       # queue starts with I
/[SZ]{2}/  # queue has consecutive 2 SZ pieces (SZ or ZS)
```

Learn more about regex at [regex101.com](https://regex101.com/).

#### Scoping

To scope these literals to check substring of the queue,

```text
<number>:<expr>
<start>-<end>:<expr>
```

```text
1:T=1             # queue starts with T
3:IJ=1            # queue has exactly 1 IJ in first 3 pieces
1-3:/SZ/          # queue has form XSZX...
3:(LJ=1||I[LJ]=1) # queue has LJ or I[LJ] in first 3 pieces
```

> **Note:** The end is exclusive, e.g. 1-3 is index 1 and index 2 pieces

Scoping is primarily useful with the count literal to require
pieces, e.g. denoting pieces that must start to build a setup.

### Combining Patterns

A comma restarts the scope of **filter**:
everything after `,` is evaluated as its own sub-pattern
before being combined with what came before.

```text
TSZ{S<Z},O{T<O} => [] 
```

Here, `O{T<O}` is evaluated as a sub-pattern, where `O` fails `T<O` (no `T` present),
so this sub-pattern generates no queues, and
the Cartesian product with `TSZ{S<Z}` is empty.

A semicolon concatenates two independent patterns

```text
TSZ{S<Z}O{T<O};T => ['TSZO', 'T']
```
