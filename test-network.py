#!/usr/bin/env python

from __future__ import print_function

# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
from imutils import paths
import numpy as np
import argparse
import random
import imutils
import numpy
import sys
import cv2

# Config
crop_start = (50, 285)
crop_size = (224, 224)
dark_factor = 0.3

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", required=True, help="path to trained model model")
ap.add_argument("-d", "--dataset", required=True, help="path to test images")
ap.add_argument("-r", "--report", required=False, help="path to report log file")
ap.add_argument("-w", "--wait", required=False, help="wait for key after each frame")
args = vars(ap.parse_args())

# Prepare crop area
crop_area = numpy.index_exp[
    crop_start[0]:crop_start[0]+crop_size[0],
    crop_start[1]:crop_start[1]+crop_size[1]
]

# load the trained convolutional neural network
print("[INFO] loading network...")
model = load_model(args["model"])

# find the image paths and randomly shuffle them
print("[INFO] loading images...")
imagePaths = sorted(list(paths.list_images(args["dataset"], contains="capture")))
print("[INFO] loaded %d images." % (len(imagePaths)))

report = sys.stdout
if args['report']:
    report = open(args['report'], "a")

index = 0
total = len(imagePaths)

for imagePath in imagePaths:
    index += 1
    # load the image
    orig = cv2.imread(imagePath)

    # pre-process the image for classification
    image = orig[crop_area]
    image = cv2.resize(image, (28, 28))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)

    # classify the input image
    (nothing, people) = model.predict(image)[0]

    # build the label
    Pmax = people
    Pmax_str = "%0.2f" % (Pmax * 100)
    if people > nothing:
        label = "People %s%%" % Pmax_str
        color = (0, 0, 255)
    else:
        label = "No-people %s%%" % Pmax_str
        color = (255, 0, 0)

    # darken the ignored image part
    output = (orig * dark_factor).astype(numpy.uint8)
    output[crop_area] = orig[crop_area]

    # put the label
    cv2.putText(output, label, (10, 25),  cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

    # show the output image
    cv2.imshow("Output", output)
    key_raw = cv2.waitKey(0)
    try:
        key = chr(key_raw)
        if key in ['d', 'D']:
            log_label = "delete"
            os.unlink(imagePath)
        elif key in ['p', 'P', 'y', 'Y']:
            log_label = "people"
        elif key in ['n', 'N']:
            log_label = "nothing"
        elif key in ['q', 'Q']:
            break
        else:
            log_label = "unknown"
        print("%s:%s:%s" % (log_label, Pmax_str, imagePath), file=report)
    except:
        pass