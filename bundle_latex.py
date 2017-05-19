#!/bin/env python
#
# NAME:
#       bundle_latex.py
#
# PURPOSE:
#       To search a LaTeX paper for accompanying filenames, get those files
#       and bundle them all together into a gzip'd tar file
#
# INPUTS:
#       main LaTeX file name (can leave off the .tex extension) (optional --
#       if no arguments given then files with .tex extension in current
#       directory will be searched for and user will be prompted for which one
#       to use)
#
#       tarfile name (optional -- if not given then the tarfile will be given
#       the same name as the main LaTeX file but with .tex replaced by
#       .tar.gz)
#
# OUTPUTS:
#       a gzip'd tarfile is created
#
# RESTRICTIONS:
#       only finds graphics files that are input via \plotone, \plottwo,
#       \includgraphics, \psfig or \epsfig commands
#       In addtion to graphics files, finds files included via \include and
#       \bibliography files.  Will not find special .sty, .cls, .clo, etc.
#       files that may be needed to compile LaTeX file.
#       Currently finds graphics files named without their extension (e.g.
#       plot for a file named plot.pdf) but without any control over which
#       extension.  That could be refined.
#
# EXAMPLE:
#       $ bundle_latex.py my_paper all_files
#       (reads my_paper.tex and creates all_files.tar.gz)
#
# MODIFICATION HISTORY:
#       Created 11/19/2009 by Jonathan D. Slavin
#       Modified 10/13/2010 -- now includes support for epsfbox name for
#           graphics files and recursive \input files (only one extra level)
#       Modified 3/24/2017 by JDS - now supports graphics file names that lack
#           their extensions, as allowed with pdflatex, though there is no
#           discernment as to the correct extension to use; simply cycles
#           through the options (eps, png,...) when searching
#       Modified 5/10/2017 -- added capability to output file names to a text
#           file.  Useful for using rsync to keep two directories in sync, for
#           example a local directory and a shared Dropbox directory
#
import os,sys,glob,tarfile,re
from argparse import ArgumentParser

# subroutine to search for LaTeX file and if multiples found, prompt for the
# user's choice
def search_for_latex():
    latex_file = ''
    files = glob.glob('*.tex')
    if files:
        print 'found {} apparent LaTeX files, choose one:'.format(files)
        n = 0
        for f in files:
            print '{} => {}'.format(n,f)
            n += 1
        nfile = int(raw_input('file no. =? :'))
        if (nfile < 0) or (nfile > (len(files) - 1)):
            print 'bad file no.'
            sys.exit(1)
        latex_file = files[nfile]
    elif len(files) == 1:
        latex_file = files[0]
    else:
        print 'no LaTeX files found in current directory'
        sys.exit(1)
    return latex_file

def find_input_files(lines):
    """Return a list of the files that are to be \input to a LaTeX file.

    The content (lines as a list) in the file are given as input and a list
    of file names (the existence of which is checked) and the expanded
    contents are returned.  The expanded contents is the original contents
    with the \input line replaced with the lines in the input file. 
    """
    file_list = []
    p = re.compile(r"\s*\\input(\s+|\{)\s*([\w.+-_]+)\}")
    exp_lines = []
    for line in lines:
        if p.search(line) != None:
            input_file = p.search(line).group(2)
            if os.path.isfile(input_file):
                file_list.append(input_file)
                new_lines = open(input_file,'r').readlines()
                if len(new_lines) > 0:
                    exp_lines = exp_lines + decomment(new_lines)
            elif os.path.isfile(input_file+'.tex'):
                file_list.append(input_file+'.tex')
                new_lines = open(input_file+'.tex','r').readlines()
                if len(new_lines) > 0:
                    exp_lines = exp_lines + decomment(new_lines)
            else:
                print 'Could not locate input file {}'.format(input_file)
        else:
                exp_lines.append(line)
    return file_list, exp_lines

def decomment(lines):
    """
    Return lines with LaTeX comments (denoted by % signs) removed
    """
    p1 = re.compile(r"^\s*%+.*$")
    # find comments within a line (not at the beginning)
    p2 = re.compile(r"[^\\]%+")
    decomlines = []
    for line in lines:
        # for lines with % as first non-space character
        if p1.match(line): continue
        # find lines with comment within the line (not at line beginning)
        s = p2.search(line)
        if s != None:
            pos = s.start() + 1
            line = line[0:pos] + '\n'
        decomlines.append(line)
    return decomlines
# main program
"""
Program to bundle up in a gzip'd tar file all files necessary to produce a
printable document from the main LaTeX file for a paper.

bundle_latex.py takes as input (optionally) the name of the main LaTeX paper
and the name of the output tar file.  
   - If no arguments are given it will look for files with .tex extension and
     prompt for the paper to use. 
   - If one argument is given it takes that as the name of the LaTeX file and
     the tar file is given the same root name (with .tar.gz added on).  (NOTE:
     The filename may be given with or without the .tex extension.  If the
     filename as given is not found then the name with .tex added on will be
     searched for.)  
   - If two arguments are given the second is used as the root name for the
     tar file (.tar.gz is added on)
"""
parser = ArgumentParser(description='Bundle files needed for LaTeX document')
parser.add_argument('latex_file', default=None, help='latex document')
parser.add_argument('tar_file', default=None, nargs='?',
        help='name for tar file')
parser.add_argument('-n', '--notar', dest='make_tar', 
        action='store_false', help='Do not create a tar file')
parser.add_argument('-o','--ofiles', action='store_true', 
    help='Output filenames to a text file (for example for use with rsync)')
parser.add_argument('-f','--fileout', help='text file name for file list',
        default='rsync_include.txt')
args = parser.parse_args()
infile = args.latex_file
tar_file = args.tar_file
make_tar = args.make_tar
ofiles = args.ofiles
fileout = args.fileout
if infile:
    latex_file = infile
    if not os.path.isfile(latex_file):
        # case where .tex was left off file name
        file_try = latex_file + '.tex'
        if os.path.isfile(file_try):
            latex_file = file_try
        else:
            print 'neither {} nor {} were found'.format(latex_file,file_try)
            latex_file = search_for_latex()
else:
    latex_file = search_for_latex()

if tar_file:
    tarfilename = tar_file
    # guard against case where user gives name with .tar or .tar.gz
    # extension
    if len(tarfilename) > 7:
        if tarfilename[-7:] != '.tar.gz' and tarfilename[-4:] != '.tar':
            tarfilename = tarfilename + '.tar.gz'
        elif tarfilename[-4:] == '.tar':
            tarfilename = tarfilename + '.gz'
    elif len(tarfilename) > 4:
        if tarfilename[-4:] != '.tar':
            tarfilename = tarfilename + '.tar.gz'
        else:
            tarfilename = tarfilename + '.gz'
    else:
        tarfilename = tarfilename + '.tar.gz'
else:
    # If no tar file name given, tar file is named after LaTeX file
    tarfilename = os.path.splitext(latex_file)[0] + '.tar.gz'

if make_tar: print "Will create gzip'd tar file named {}".format(tarfilename)
tarfiles = [latex_file]
# we found (or were passed) the LaTeX file, now we search it for any necessary
# inputs
with open(latex_file,'r') as f:
    all_lines = f.readlines()

# remove comment lines before looking for \input declarations
lines = decomment(all_lines)

# search for \input lines
file_list, exp_lines = find_input_files(lines)
lines = exp_lines
missinp = []
for input_file in file_list:
    if os.path.isfile(input_file):
        tarfiles.append(input_file)
        file_lines = open(input_file,'r').readlines()
        file_lines = decomment(file_lines)
        extra_files, exp_lines = find_input_files(file_lines)
        # note: we only go two levels down -- i.e. we find files to be
        # included by \input in the root file and files to be included by
        # \input in those files -- but not any levels below that
        for ef in extra_files:
            if os.path.isfile(ef):
                tarfiles.append(ef)
            else:
                print 'input file not found: {}'.format(ef)
                missinp.append(ef)
        lines = lines + decomment(exp_lines)
    else:
        print 'input file not found: {}'.format(ef)
        missinp.append(ef)

if missinp:
    print 'The following input file(s) were not found:'
    for m in missinp:
        print m

# search for graphics files
# acceptable file names can include alphanumeric characters and the characters
# +, -, _, and .  They are required to start with an alphanumeric character
# I think that covers it though there could be exotic names (e.g. with @, $,
# :, etc. in their names) 
p1 = re.compile(r'\\includegraphics.*\{(\w+[-+_.\w]*)\}')
p2 = re.compile(r'\\plotone\{(\w+[-+_.\w]*)\}')
p3 = re.compile(r'\\plottwo\{(\w+[-+_.\w]*)\}\{(\w+[-+_.\w]*)\}')
# epsfig and psfig can take extra arguments -- so need to avoid taking those
# as part of the file name and to include cases where such arguments are
# present -- thus the .* after the ) and before the }
# this won't catch cases that don't list figure=filename as the first argument
p4 = re.compile(r'\\epsfig\{figure=(\w+[-+_.\w]*).*\}')
p5 = re.compile(r'\\psfig\{figure=(\w+[-+_.\w]*).*\}')
p6 = re.compile(r'\\epsfbox\{(\w+[-+_.\w]*)\}')
missing = []
for line in lines:
    if p1.search(line):
        graphics_files = [p1.search(line).group(1)]
    elif p2.search(line):
        graphics_files = [p2.search(line).group(1)]
    elif p3.search(line):
        graphics_files = list(p3.search(line).groups())
    elif p4.search(line):
        graphics_files = [p4.search(line).group(1)]
    elif p5.search(line):
        graphics_files = [p5.search(line).group(1)]
    elif p6.search(line):
        graphics_files = [p6.search(line).group(1)]
    else:
        graphics_files = []
    for f in graphics_files:
        root,ext = os.path.splitext(f)
        if not ext:
            # May want to improve this by adding an option to only look for
            # graphics files with a particular extension - e.g. pdf if using
            # pdflatex or eps if using latex
            ffound = False
            for ext in ['pdf','png','jpg','eps']:
                fname = f + '.' + ext
                if os.path.isfile(fname):
                    tarfiles.append(fname)
                    ffound = True
                    break
            if not ffound:
                print 'Could not locate graphics file {}'.format(f)
                missing.append(f)
        else:
            if os.path.isfile(f):
                tarfiles.append(f)
            else:
                print 'Could not locate graphics file {}'.format(f)
                missing.append(f)
if missing:
    print 'The following graphics files were not found:'
    for m in missing:
        print m
# search for bibliography file info
for line in lines:
    i = line.find('\\bibliography{')
    if i != -1: 
        i1 = line.find('{')
        i2 = line.find('}',i1)
        bibfiles = line[i1+1:i2].split(',')
        for bibfile in bibfiles:
            bibfile = bibfile + '.bib'
            if os.path.isfile(bibfile):
                tarfiles.append(bibfile)
            else:
                print 'Could not locate bibliography file {}'.format(bibfile)
if make_tar:
    print 'Writing tar file {}'.format(tarfilename)
    tar = tarfile.open(tarfilename,'w:gz')
    for tf in tarfiles:
        print tf
        tar.add(tf)
    tar.close()
else:
    missing = []
    for f in tarfiles:
        if not os.path.isfile(f):
            print 'file {} not found'.format(f)
            missing.append(f)
        else:
            print 'file {} is present'.format(f)
    if len(missing) > 0:
        print 'The following files were not found:',missing

# Output the file names to the text file named fileout.  The main purpose of
# this is for using rsync to keep a document and all its associated files
# synced between two directories.  To do that one would do:
# $ rsync --files-from='rsync_include.txt' -av . dest_directory (where
# dest_directory is the destination directory and ends with a /)
if ofiles:
    # Note: this will overwrite fileout (rsync_include.txt by default)
    with open(fileout,'w') as fo:
        for tf in tarfiles:
            fo.write(tf+'\n')
        print 'file names output to {}'.format(fileout)
