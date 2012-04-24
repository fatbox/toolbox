#!/usr/bin/env python
"""
Sync two block devices only copying changed blocks

Based losely on the script here:
http://www.bouncybouncy.net/ramblings/posts/xen_live_migration_without_shared_storage/

However, this version is aimed at two local block devices instead of
two devices via ssh.
"""

import hashlib
import sys
import os

def do_open(name, mode):
    """
    Open a file in mode and return the handle and size
    """
    f = open(name, mode)
    f.seek(0, 2)
    size = f.tell()
    f.seek(0)
    return f, size

def sync(source, dest, blocksize):
    # open our source & dest
    src, src_size = do_open(source, 'r')
    dst, dst_size = do_open(dest, 'r+')

    # ensure that their sizes match
    # we can't sync if they're different sizes
    assert src_size == dst_size

    same_blocks = diff_blocks = 0

    while 1:
        s_block = src.read(blocksize)
        d_block = dst.read(blocksize)

        if not s_block:
            break

        # calculate our hash sums
        s_sum = hashlib.md5(s_block).digest()
        d_sum = hashlib.md5(d_block).digest()

        if s_sum != d_sum:
            # the blocks don't match
            diff_blocks += 1

            # seek back blocksize on the destination and re-write the block
            dst.seek(-blocksize, 1)
            dst.write(s_block)
        else:
            same_blocks += 1

        print "same: %d - diff: %d - %d/%d" % (same_blocks, diff_blocks, same_blocks+diff_blocks, src_size / blocksize),
        print

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] /dev/source /dev/dest")
    parser.add_option("-b", "--blocksize", dest="blocksize", action="store", type="int", help="block size", default=1024*1024)
    (options, args) = parser.parse_args()

    if len(args) != 2:
        parser.print_help()
        sys.exit(1)

    source = args[0]
    dest = args[1]

    assert os.access(source, os.R_OK)
    assert os.access(dest, os.W_OK)

    sync(source, dest, options.blocksize)
