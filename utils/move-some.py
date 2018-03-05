#!/usr/bin/env python3

import sys
import os
import glob
import random

try:
    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    count = int(sys.argv[3])
except:
    sys.stdout.write("Usage: %s <src_dir> <dst_dir> <count>\n" % sys.argv[0])
    sys.exit(1)

src_list = glob.glob(src_dir + "/*.jpg", recursive = True)
random.shuffle(src_list)

for fn in src_list[:count]:
    fnn = dst_dir + "/" + os.path.basename(fn)
    print("%s -> %s" % (fn, fnn))
    os.rename(fn, fnn)
