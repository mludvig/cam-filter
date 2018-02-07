#!/usr/bin/env python

import os
import sys
import numpy
import cv2
from imutils import paths

# Config
#crop_start = (50, 280)
crop_start = (53, 268)
crop_size = (224, 224)
dark_factor = 0.3

# Prepare crop area
crop_area = numpy.index_exp[
    crop_start[0]:crop_start[0]+crop_size[0],
    crop_start[1]:crop_start[1]+crop_size[1]
]

# find the image paths and randomly shuffle them
print("# loading images...")
imagePaths = sorted(list(paths.list_images(sys.argv[1], contains="capture")))
print("# loaded %d images." % (len(imagePaths)))

for imagePath in imagePaths:
    image = cv2.imread(imagePath)
    orig = image[crop_area]
    image = (image * dark_factor).astype(numpy.uint8)
    image[crop_area] = orig
    cv2.imshow("Output", image)
    key_raw = cv2.waitKey(0)
    try:
        key = chr(key_raw)
        if key in ['d', 'D']:
            print("delete:%s" % imagePath)
            os.unlink(imagePath)
        elif key in ['p', 'P', 'y', 'Y']:
            print("people:%s" % imagePath)
        elif key in ['n', 'N']:
            print("nothing:%s" % imagePath)
        else:
            print("unknown:%s" % imagePath)
    except:
        pass
