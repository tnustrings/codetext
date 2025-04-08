# codetext

code with text (vscode extension
[here](https://github.com/tnustrings/ct-vscode)).

codetext lets you embed code in text like images or figures floating
in a document. it's a bit like jupyter notebooks with the addition
that code chunks are named and you can use the names to nest chunks.

here's an example:

```
begin a file named foo.py.

``//foo.py: #py
print("ooh, baby you're a fool to py") 
if bar {
  ``bar``
}
``

when we open a chunk for the first time, like //foo.py above,
it is followed by a colon.

the preceeding // in //foo.py marks this code chunk as a file root.

chunk names are noted as paths, e.g. /bar for the chunk named bar in
the last opened file. we put some code into the /bar chunk.

the #py signals the programming language for syntax highlighting, you
can leave it out.

``/bar: #py
   print("my bar")
   ``baz``
   ``boz``
``

we can use relative paths and reference the previous chunk (/bar) via .

``./baz: #py
   my = "baz code"
``

this would be baz' absolute path:

``/bar/baz #py
   and it makes me 
``

this appends to the baz chunk. when we append, we don't write the
colon after the chunk name.

this would be it's path starting from the file:

``//foo.py/bar/baz #py
   wonder why
``

when we don't give a path we append to the same chunk.

`` #py
   print("still my baz code.")
``

if we would like to change to baz's sibling boz now, we could say
../boz, /bar/boz, //foo.py/bar/boz or /*/boz, if boz's name is unique
in foo.

``/*/boz: #py
   print("in boz")
``

if there's a loop etc, and we would like the next unnamed chunk in the
text to be inside the loop instead of appended to the end of the chunk
we can say ``.``:

`` #py
   for i = 0; i < n; i++ {
      ``.``
   }
``

then the following chunk will be put where the ``.`` tag is and not to
the end of the chunk.

`` #py
   print("inside the loop")
``

go back via ..

``../ #py
   print("appending to the foo/bar/baz code again")
``

we open a second file, named zoo.py.

``//zoo.py: #py
  welcome to the zoo
  ``dolphins``
``

now the last opened file is zoo.py, so /dolphins takes us to the chunk in zoo.py

``/dolphins: #py
  print("are there dolphins in the zoo?")
``

if you'd like to switch back to foo.py like this:

``//foo.py #py
  print("hello foo again")
``

if there's only one output file in the codetext and if you don't give
this file an alias, you leave out its name when referring to child
chunks, otherwise you include it like above.

```

`foo.ct` contains the above example. you can assemble `foo.py` and
`zoo.py` by saying `ct foo.ct`.

## install

download the [latest
release](https://github.com/tnustrings/codetext/releases) and install
with pip:

```
$ pip install ct-<version>-py3-none-any.whl
```

## dev

build:

```
$ python -m build
```

for some of the latex commands used in generating the doc, see
[`tex.md`](tex/tex.md).

## issues

codetext takes a chunk's indent from the first chunk line, and tries
to fill up accordingly. if you write chunks that are already indented,
take care that the first line is indented like the rest of the chunk,
so that codetext doesn't think it needs to indent when it actually
doesn't need to.

fix: allow dashes in filename (-)

