# bundle_latex
a small python script aimed at gathering up all the files necessary for compiling a LaTeX document

Takes a LaTeX file as input and searches it for all the files that need to be included for it to compile, 
including image files, .bib files and /input files

It can create a tar file including all the files or write out a file list (useful for rsync'ing)

Currently only for python 2.7.x.  I plan to make it either only for 3.x or compatible with both.
