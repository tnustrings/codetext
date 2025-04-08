# __main__ kicks off ct from command line and python -m

import sys
from ct import ct, tex, org
import argparse
import os.path

# main kicks off tangling
def main():

    # parse the command line argument(s)
    parser = argparse.ArgumentParser()

    # the .ct file
    parser.add_argument("ct_file", nargs="?", help="codetext file")
    # optional generated file
    parser.add_argument("generated_file", nargs="?", help="go to line number from generated file in ct") 
    # optional line number in generated file
    parser.add_argument("line_number", nargs="?", help="line number from generated file")
    parser.add_argument("--tex", help="print doc as latex", action="store_true") 
    parser.add_argument("--from-org", help="input is a .org file", action="store_true")
    parser.add_argument("--mdtotex", nargs=1, help="for latex doc generation. a command to convert markdown between codechunks to tex, e.g. 'pandoc -f markdown -t latex'")
    parser.add_argument("--shell", action="store_true", help="run mdtotex command as shell script.")
    parser.add_argument("-o", help="latex template out file, if run with --tex and without ct_file")
    parser.add_argument("--header", help="latex template header file")
    parser.add_argument("--lower", action="store_true", help="lowercase tex template")

    args = parser.parse_args()

    # no ct file and --tex? generate latex template and header
    if args.ct_file is None:
        if args.tex:
            tmpl = tex.gettemplate(header=args.header)
            header = tex.getheader(lowercase=args.lower)

            # write template and header
            # notify if the files is already there
            checkoverwrite(args.o, tmpl)
            checkoverwrite(args.header, header)

        return

    f = args.ct_file
    text = open(f).read()
    f.close()
    
    # is text in org format? convert it to ct format
    if args.from_org:
        text = org.orgtoct(text)
        # print(text)
        
    # normal compilation
    if args.generated_file is None:
        if args.tex == True:
            # run ct and print tex
            # args.mdtotex seems to be a string array
            tex.printtex(text, mdtotex=args.mdtotex, shell=args.shell) # todo maybe print(tex.totex(text))
        else:
            # run ct and write files
            ct.ctwrite(text)
    elif args.line_number: # todo change this to if args.line_number is not None
        # map from line number in generated source to original line number in ct

        # run ct without writing files
        ct.ct(text)

        # print the original line number
        print(ct.ctlinenr[args.generated_file][args.line_number-1]) # line numbers are 0-indexed

# checkoverwrite writes text to a file and asks before whether an existing file should be overwritten
def checkoverwrite(path, text):
    if os.path.isfile(path):
        resp = input(f"the file {path} already exists. overwrite it? [Y/n]: ")
        if resp == "Y":
            with open(path, "w") as f:
                f.write(text)


sys.exit(main())


