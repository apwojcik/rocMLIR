#!/usr/bin/env python

"""
This tool is for selectively patching a tree of source code.  It
takes as input a list of files to operate on and two directory
locations (src and dst).  It uses a diff of the relative src and
dst files, and patches the respective dst file.  If the specific
src file is empty, this tool will remove the file in the dst tree.
"""

import os
import argparse
from pathlib2 import Path
from diff_match_patch import diff_match_patch

class SrcTreePatcher:
    
    def __init__(self, file_list, src_dir_prefix, dst_dir_prefix):
        self.file_list = file_list
        self.src_dir_prefix = src_dir_prefix
        self.dst_dir_prefix = dst_dir_prefix
        self.dmp = diff_match_patch()
        
    def generate_patchset(self, upstream_text, local_text):
        """Given two file paths, generate a patchset (unified diff)."""        
        # Do the diff
        self.patch = self.dmp.patch_make(upstream_text, local_text)

    def apply_patchset(self, in_text, out_file_path=None):
        """Using a patchset, apply the patches to the given text"""
        self.out_text, self.results = self.dmp.patch_apply(self.patch, in_text)
        if (not all(self.results)):
            print("Some results were false!")
            sys.exit()
        if (out_file_path):
            with open(out_file_path, "w") as ofile:
                ofile.write(self.out_text)

    def dump(self):
        """Print everything."""
        #print("patch_toText():\n" + self.dmp.patch_toText(self.patch))
        print("patched out_text:\n" + self.out_text)
        #print("patch results:\n" + str(self.results))

    def patch_all(self):
        """Using a list of relative file paths, generate a patchset (unified diff)."""

        for rel_fname in self.file_list:
            # Set up paths
            src_path = self.src_dir_prefix + rel_fname
            dst_path = self.dst_dir_prefix + rel_fname
            print("Patching: " + dst_path + " , using " + src_path)

            # Handle dst file
            try:
                with open(dst_path, 'r') as file1:
                    dst_text = file1.read()
            except IOError as e:
                # If the dst file DNE, just create an empty one
                Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
                Path(dst_path).touch()
                print("Created the missing dst file: " + dst_path)

            # Handle src file
            try:
                with open(src_path, 'r') as file2:
                    # If src file is empty, this signifies we should
                    # delete the dst file
                    if os.path.getsize(src_path) == 0:
                        os.remove(dst_path)
                        print("Removed dst due to empty src: " + dst_path)
                        return
                    src_text = file2.read()
            except IOError as e:
                print("Could not open or read file (%s)" % e)
                #sys.exit()

            #print("dst_text:\n" + dst_text)
            #print("src_text:\n" + src_text)
            
            # Do the diff
            self.generate_patchset(dst_text, src_text)
            self.apply_patchset(dst_text, dst_path)
            #self.dump()


def main():

    # Get the path to a file containing a list of files, with each line
    # containing a relative path to the file to be patched
    parser = argparse.ArgumentParser(description='Selectively apply patches based on a file list and src/dst directories.')
    parser.add_argument('--infile', required=True, help='file containing a list of files to patch')
    parser.add_argument('--srcdir', required=True, help='path to the top-level src dir')
    parser.add_argument('--dstdir', required=True, help='path to the top-level dst dir')
    args = parser.parse_args()

    # Append "/" to dirs if not already there
    # FIXME: not portable
    args.srcdir = args.srcdir + '/' if not args.srcdir.endswith('/') else args.srcdir
    args.dstdir = args.dstdir + '/' if not args.dstdir.endswith('/') else args.dstdir

    print("infile path: " + args.infile)
    print("srcdir path: " + args.srcdir)
    print("dstdir path: " + args.dstdir)

    # Get the list of relative file paths
    flist = open(args.infile).read().splitlines()
    print("Files to patch:  " + str(flist))

    # Patch all files in the list
    stp = SrcTreePatcher(flist, args.srcdir, args.dstdir)
    stp.patch_all()


if __name__ == "__main__":
    main()
