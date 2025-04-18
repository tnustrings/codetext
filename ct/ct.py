# ct.py: codetext tangle with chunkname paths
# usage: ct.main("file.ct")

# for codetext syntax, see readme.md


# imports

import re
import sys
# from typing import Self # to reference Node type in Node
from typing_extensions import Self # support python prior to 3.11
import array

""" code-chunks are represented as nodes in a tree. """
class Node: 
    def __init__(self, name: str, parent: Self):
        # the node's name.

        # if it's a ghost node, the name starts with . and is followed by the node's index in its parent's ghostchilds.
        # although ghost names can never be used to reference or go to a ghost node it's handy if the names of a node's ghostchilds are distinct for latex links # to js
        self.name = name
        
        self.cd = {}
        self.cd["."] = self
        if parent == None:
            self.cd[".."] = self
        else:
            self.cd[".."] = parent

        # keep the text as lines, cause splitting on '\n' on empty text gives length 1 (length 0 is wanted)
        self.lines = []
        # the ghost children. why more than one?
        self.ghostchilds = []
        # for each text line, ctlinenr holds its original line nr in ct file
        self.ctlinenr = {}
        # has this node been declared by a colon ':'
        self.hasbeendeclared = False

        # at which line of the parent is the child?
        self.lineinparent = None
        
        # at these ct lines, there are children { int -> Node }
        self.childatctline = {}

        # nchunks: the number of code chunks appended to this node
        self.nchunks = 0

        # this node is referenced from the ith chunk in the parent node
        self.iparentchunk = None
        
    # ls lists the named childs
    def ls(self):
        # return all except . and ..
        return [k for k in self.cd.keys() if k != "." and k != ".."]

    # is root says whether it's a root node, that means if it's parent
    # is itself
    def isroot(self):
        return self.cd[".."] == self

# debug offers a turn-offable print
def debug(s: str):
    i = 0
    print(s)
    
# isname returns true if line is the referencing name line of a code chunk
def isname(line: str) -> bool:
    # the name needs to contain at least one non-tick to distinguish it from three-tick ``` markdown code-block openings
    ret = bool(re.match(r".*``[^`]+``", line))
    # debug(f"isname {line}: {ret}")
    return ret

# isdblticks says if the line consists of two ticks only (not considering programming-language hashtag)
# this could either be a start line of an unnamed chunk or an end line of a chunk
def isdblticks(line: str) -> bool:
    # return re.match(r"^@$", line) # only allow single @ on line, to avoid mistaking @-code-annotations for doku-markers
    ret = bool(re.match(r"^``(\s+#\w+)?$", line))
    #debug(f"isend {line}: {ret}")
    return ret

# isghost says whether it's a ghost-name (starting with a .) # to js
def isghost(name: str) -> bool:
    # check that it's not a dot followed by a non-dot, maybe it would be enough to check that it's not a dot followed by a number.
    return bool(re.match(r"^\.[^\.]", name))

# fromroot says whether the name starts from a root
def fromroot(name: str) -> bool:
    ret = bool(re.match(r"^//", name))
    #debug(f"isroot {name}: {ret}")
    return ret

# getname gets the chunkname from a chunk-opening or in-chunk reference
def getname(line: str) -> str:
    # remove the leading ticks (openings and references)
    name = re.sub(r"^[^`]*``", "", line, 1) # 1: count
    # remove the trailing ticks (references only)
    name = re.sub(r"``.*", "", name)
        
    # remove the newline (openings only)
    name = re.sub(r"\n$", "", name)
    # remove the programming language hashtag (if there) (openings only)
    name = re.sub(r"\s+#\w+$", "", name)

    # don't remove the declaration colon, we need it in put()
    
    # debug(f"getname({line}): '{name}'")

    return name

# save the ctlines for printtex
# lines keep their \n
ctlines = []

# for each generated file, map its line numbers to the original line
# numbers in ct file
ctlinenr = {}

# the name of ghost nodes
# GHOST = "#" # to js

# assemble assembles a codechunk recursively, filling up its leading
# space to leadingspace. this way we can take chunks that are already
# (or partly) indented with respect to their parent in the editor, and
# chunks that are not. 
def assemble(node: Node, leadingspace: str, rootname: str, genlinenr: int) -> (str, int):

    global ctlinenr

    # if it's a ghost node, remember the last named parent up the tree
    # if node.name == GHOST:
    if isghost(node.name): # to js
        lnp = lastnamed(node)
        
    """ 
    find out a first line how much this chunk is alredy indented
    and determine how much needs to be filled up
    """
    # leading space already there (in first line)
    if len(node.lines) > 0:
        alreadyspace = re.search(r"^\s*", node.lines[0]).group()
    else:
        alreadyspace = "" # no line, so no leading space already there
    # space that needs to be added
    addspace = leadingspace.replace(alreadyspace, "", 1) # 1: replace once

    # if the rootname isn't in ctlinenr yet, put it there
    if not rootname in ctlinenr:
        ctlinenr[rootname] = {}

    out = ""
    ighost = 0 
    # for line in lines:
    for i, line in enumerate(node.lines):
        if isname(line):

            # remember leading whitespace
            childleadingspace = re.search(r"^\s*", line).group() + addspace
            # print("#getname 1")
            name = getname(line)
            if name == ".":   # assemble a ghost-child
                (outnew, genlinenr) = assemble(node.ghostchilds[ighost], childleadingspace, rootname, genlinenr) 
                out += outnew #  + "\n" # why add \n?
                ighost += 1
            else:             # assemble a named child
                # if node.name == GHOST:
                if isghost(node.name): # to js
                    # if we're at a ghost node, we get to the child via the last named ancestor
                    child = lnp.cd[name]
                else:
                    child = node.cd[name]
                (outnew, genlinenr) = assemble(child, childleadingspace, rootname, genlinenr) 
                out += outnew # + "\n" # why add \n?
        else: # normal line
            out += addspace + line + "\n"
            # map from the line number in the generated source to the original line number in the ct
            ctlinenr[rootname][genlinenr] = node.ctlinenr[i]
            genlinenr += 1 # we added one line to root, so count up

    # return the generated text and the new root line number (should be the same as the number of lines in out, so maybe don't return it?)
    return (out, genlinenr)

currentnode = None # the node we're currently at
openghost = None # if the last chunk opened a ghostnode, its this one

# put puts text in tree under relative or absolute path
def put(path: str, text: str, ctlinenr: int) -> None:
    global openghost
    global currentnode

    # debug("put(" + path + ")")

    # create a ghostnode if called for
    if (path == "." or path == "") and openghost != None:
        currentnode = openghost

        # we enter the ghost node the first time, this implicitly declares it
        currentnode.hasbeendeclared = True
        
        openghost = None # necessary?
    else:
        # named node (new or append) or ghost node (append)

        # if the path would need a node to cling to but there isn't one
        if currentnode is None and not fromroot(path):
            print(f"error (line {ctlinenr}): there's no file to attach '{path}' to, should it start with '//'?")
            exit

        # a colon at the path end indicates that this is a declaration
        isdeclaration = bool(re.search(r":\s*$", path))

        # remove the colon from path
        path = re.sub(r":\s*$", "", path)

        # find the node, if not there, create it
        node = cdmk(currentnode, path, ctlinenr)

        # we'd like to check that a node needs to have been declared with : before text can be appended to it. for that, it doesn't help to check if a node is there, cause it might have already been created as a parent of a node. so we introduce a node.hasbeendeclared property.

        if isdeclaration and node.hasbeendeclared:
            print(f"error (line {ctlinenr}): chunk {path} has already been declared, maybe drop the colon ':'")
            exit
        elif not isdeclaration and not node.hasbeendeclared:
            print(f"error (line {ctlinenr}): chunk {path} needs to be declared with ':' before text is appended to it")
            exit

        # set that the node has been declared
        if isdeclaration:
            node.hasbeendeclared = True

        # all should be well, we can set the node as the current node
        currentnode = node

    # append the text to node
    concatcreatechilds(currentnode, text, ctlinenr)


# cdmk walks the path from node and creates nodes if needed along the way.
# it returns the node it ended up at
def cdmk(node: Node, path: str, ctlinenr: int) -> Node:

    # if our path is absolute (starting from a root), we can't just jump to the root, because when changing positions in the tree, we need to make sure that ghostnodes are exited properly.  cdone takes care of that, so we go backward node by node with cdone.  cdroot does this recursively.
    if re.match(r"^/", path):
        # exit open ghost nodes along the way
        node = cdroot(node, ctlinenr)

    # if the path starts with // we might need to change roots.
    if re.match(r"^//", path):

        # remove the leading // of root path
        path = path.strip("/")
    
        # split the path
        p = path.split("/")

        # the first part of the path is the rootname
        rootname = p[0]

        # root not there? create it
        if not rootname in roots:
            roots[rootname] = Node(rootname, None)

        # set the node to the root
        node = roots[rootname]

        # stitch the rest of the path together to walk it
        path = "/".join(p[1:])

    # for absolute paths, we should be at the right root now

    # remove leading / of absolute path
    path = path.strip("/")

    # follow the path
        
    elems = path.split("/")

    search = False # search for the next name
    for elem in elems:
        # do we start a sub-tree search?
        if elem == "*":
            search = True
            continue
        if search == True:
            # search for the current name
            search = False # reset
            res = []
            bfs(node, elem, res) # search elem in node's subtree
            if len(res) > 1:
                print(f"error (line {ctlinenr}): more than one nodes named {elem} in sub-tree of {pwd(node)}")
                exit
            elif len(res) == 0:
                print(f"error (line {ctlinenr}): no nodes named {elem} in sub-tree of {pwd(node)}")
                exit
            else:
                node = res[0]
            continue

        # standard:
        # walk one step
        walk = cdone(node, elem, ctlinenr)
        # if child not there, create it
        if walk == None:
            walk = createadd(elem, node)
        node = walk

    # print("put return: " + str(node.name))
    return node # the node we ended up at

# bfs breath-first searches for all nodes named 'name' starting from 'node' and puts them in 'out'
def bfs(node: Node, name: str, out: array.array) -> None:
    #    print(f"bfs {node}")
    if node.name == name:
        out.append(node)
    # search the node's childs
    for childname in node.ls():
        bfs(node.cd[childname], name, out)
    # do we need to search the gostchilds?
    for child in node.ghostchilds:
        bfs(child, name, out)

# cdroot cds back to root. side effect: ghosts are exited
def cdroot(node: Node, ctlinenr: int = None) -> Node:
    if node == None: return None
    if node.cd[".."] == node: # we're at a root
        return node
    # continue via the parent
    return cdroot(cdone(node, "..", ctlinenr)) # it's probably not very necessary to pass the ctlinenr here, cause it only check's that the step isn't a '#' that would walk into a ghostnode
    
# cdone walks one step from node
def cdone(node: Node, step: str, ctlinenr: int = None) -> Node:
    #if step == GHOST:
    if isghost(step): # to js
        # we may not walk into a ghost node via path
        print(f"error (line {ctlinenr}): node names starting with . are not allowed.") # to js
        exit
    if step == "":
        step = "."
    if step == "..": # up the tree
        # debug(f"call exitghost for {pwd(node)}")
        exitghost(node)

    if step in node.cd:
        return node.cd[step]
    
    return None
    
# exitghost moves ghost node's named children to last named parent. needs to be called after leaving a ghost node
def exitghost(ghost: Node) -> None:
    # not a ghost? do nothing
    #if ghost == None or ghost.name != GHOST:
    if ghost == None or not isghost(ghost.name): # to js
        return
    #debug("exitghost")

    """ if we exit a ghost node, we move all its named childs to the ghost node's parent so that they can be accessed from there and let the ghostnode be the childs' ghostparent (from where they can get e.g. their indent) """
    # for name, child in node.namedchilds.items():
    for name in ghost.ls():
        child = ghost.cd[name]
        child.ghostparent = ghost
        # set child's parent to ghost's parent
        child.cd[".."] = ghost.cd[".."]
        """ when putting the child in the parent's namedchilds, we don't need to worry about the name already being taken, because we moved every child that could be touched here that was already there inside the ghostnode upon creating it. """
        # hang the child to ghost's parent
        parent = ghost.cd[".."]
        parent.cd[name] = child
        # delete child from ghost
        del ghost.cd[name]

# pwd: print the path to a node starting from its root
def pwd(node: Node) -> str:
    out = node.name
    walk = node
    # append the name of each parent node to the left side of path
    while walk.cd[".."] != walk: # todo maybe say while not walk.isroot()
        walk = walk.cd[".."]
        out = walk.name + "/" + out
    # append the file marker
    if walk.name in roots: # root check necessary?
        out = "//" + out
    return out

# createadd creates a named or ghost node and adds it to its parent
def createadd(name: str, parent: Node) -> Node:

    node = Node(name, parent)
    # debug(f"createadd: {pwd(node)}")
    
    # if we're creating a ghost node
    # if node.name == GHOST:
    if isghost(node.name): # todo isghost(name) function? todo add to js
        # debug(f"creating a ghost child for {parent.name}")
        # add it to its parent's ghost nodes
        parent.ghostchilds.append(node)
    else:
        # we're creating a name node
        
        """ if the parent is a ghost node, this node could have already been created before with its non-ghost path (an earlier chunk in the codetext might have declared it and put text into it, with children/ghost children, etc), then we move it as a named child from the last named parent to here """
        # if a node with this name is already child of last named parent, move it here
        #if parent.name == GHOST:
        if isghost(parent.name): # to js
            lnp = lastnamed(node)
            if node.name in lnp.ls():
                node = lnp.cd[name]
                del lnp.cd[name]
                node.cd[".."] = parent

        # add named node to parent, if it was created or moved
        parent.cd[name] = node

    return node

# concatcreatechilds concatenates text to node and creates children from text (named or ghost)
# this is the only place where text gets added to nodes
def concatcreatechilds(node: Node, text: str, ctlinenr: int) -> None:
    global openghost
    openghost = None # why here? not so clear. but we need to reset it somewhere, that only the direct next code chunk can fill a ghost node

    # replace the last \n so that spli doesn't produce an empty line at the end
    text = re.sub(r"\n$", "", text)
    newlines = text.split("\n")

    # map from the line number in node to original line number in ct (get existing line count before new lines are added to node)
    N = len(node.lines)
    for i, _ in enumerate(newlines):
        # go through the new lines
        node.ctlinenr[N+i] = ctlinenr + i
        # map from the ct line to the node
        nodeatctline[ctlinenr + i] = node

    # also set nodeatctline for the opening and the closing line of a chunk todo add to js
    # opening line
    nodeatctline[ctlinenr - 1] = node
    # closing line
    nodeatctline[ctlinenr + len(newlines)] = node
        
    #debug("N: " + str(N))
    #debug("node.ctlinenr: " + str(node.ctlinenr))

    # put the new lines into node
    node.lines.extend(newlines)

    # generate the child nodes
    for i, line in enumerate(newlines):
        if not isname(line):
            continue
        """ why do we create the children when concating text? maybe because here we know where childs of ghost nodes end up in the tree. """

        # the newly created child
        child = None

        name = getname(line)
        if name == ".": # ghost child
            # if we're not at the first ghost chunk here
            if openghost != None:
                print(f"error (line {ctlinenr+i}): only one ghost child per text chunk allowed")
                exit
            # create a ghost chunk
            # it's name is a dot followed by it's index in the parent's ghostchilds array
            # openghost = createadd(GHOST, node)
            openghost = createadd("." + str(len(node.ghostchilds)), node) # todo to js
            child = openghost
        else: # we're at a name
            # if name not yet in child nodes
            if not name in node.ls():
                # create a new child node and add it
                child = createadd(name, node)
        
        # at which line of the parent is the child?
        child.lineinparent = i+N

        # at this line, the parent has a child
        node.childatctline[ctlinenr+i] = child

        # we're just appending the nth chunk of this node, this is the
        # chunk that references to the child (used for linking to the
        # specific parent chunk in doc)
        child.iparentchunk = node.nchunks

    # we've appended a codechunk to the node, so increase the number of chunks
    # do this after child.iparentchunk was set in the loop
    node.nchunks += 1

# lastnamed returns the last named parent node
def lastnamed(node: Node) -> Node:
    if node == None: return None
    # if node.name != GHOST: return node
    if not isghost(node.name): return node # to js
    return lastnamed(node.cd[".."])

# the root nodes
roots = {}

# the node at a ct line (if there is one)
nodeatctline = {}


# printtree: print node tree recursively
def printtree(node: Node) -> None:
    print(f"printtree of {node.name}")
    print(f"ls: {node.ls()}")
    for name in node.ls():
        printtree(node.cd[name])
    for child in node.ghostchilds:
        printtree(child)

# is this ctline opening a chunk?
ischunkopening = {} # int to bool
# is this ctline closing a chunk?
ischunkclose = {} # int to bool
        

# ct runs codetext for file
# todo change to take text?
def ct(text) -> None:

    global roots, roottext, currentnode, openghost, ctlinenr, nodeatctline, ctlines, ischunkopening, ischunkclose
    
    # reset variables
    roots = {}
    roottext = {}
    currentnode = None
    openghost = None
    ctlinenr = {}
    nodeatctline = {}
    ctlines = []
    ischunkopening = {}
    ischunkclose = {}

    # f.readlines() # readlines keeps the \n for each line, 
    lines = text.split("\n")
    # put the \n that split removed back to each line, text concat in nodes relies on that.
    for (i, _) in enumerate(lines):
        lines[i] += "\n"

    # save the lines, for totex or so
    ctlines = lines
    
    # put in the chunks

    # are we in chunk?
    inchunk = False
    # current chunk content
    chunk = ""
    # current chunk name/path
    path = None
    # start line of chunk in ct file
    chunkstart = 0
    
    for i, line in enumerate(lines):

        """we can't decide for sure whether we're opening or closing a chunk by looking at the backticks alone, cause an unnamed chunk is opend the same way it is closed.  so in addition, check that inchunk is false."""
        if bool(re.search(r"^``[^`]*", line)) and inchunk is False:
            # we're in a chunk
            inchunk = True
            # remember its path
            path = getname(line)
            # remember the start line of chunk in ct file
            # add one for the chunk text starts in the next line, not this
            # (treat the line numbers as 0-indexed)
            chunkstart = i+1 

            # remember that this line is opening a chunk
            ischunkopening[i] = True
            
        elif isdblticks(line): # at the end of chunk save chunk
            inchunk = False
            # debug(f"calling put for: {path}")
            # debug("split chunk: " + str(chunk.split("\n")))
            put(path, chunk, chunkstart)
            # reset variables
            chunk = ""
            path = None

            # remember that this line is closing a chunk
            ischunkclose[i] = True

        elif inchunk: # when we're in chunk remember line
            chunk += line
        #else:
        #    debug(line, end="") # for debugging


    """ in the end we need to exit all un-exited ghost nodes so that their
    named children end up as the named children of the last named parent
    where we can access them.  """

    cdroot(currentnode)

    """ at the end, write all files (each file is a root) """
    for filename in roots:
        # todo: add don't edit comment like before
        
        # assemble the code
        (out, _) = assemble(roots[filename], "", filename, 1)
        # printtree(roots[filename])
        
        # save the generated text
        roottext[filename] = out # todo error out is a tuple?

        

# ctwrite runs codetext and writes the assembled files        
def ctwrite(text, dir=None):

    # run codetext
    ct(text)

    # write the assembled text for each root
    for filename in roots:
        
        # assemble the code
        txt = roottext[filename]
        # printtree(roots[filename])

        path = filename
        # and write it to file
        if dir is not None:
            path = dir + "/" + filename
        with open(path, "w") as f:
            f.write(txt)

            # say which file was written
            print(path)


