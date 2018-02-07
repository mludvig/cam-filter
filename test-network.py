#!/usr/bin/env python

# USAGE
# python test_network.py --model santa_not_santa.model --image images/examples/santa_01.png

# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
from imutils import paths
import numpy as np
import argparse
import random
import imutils
import numpy
import cv2

# Config
#crop_start = (50, 280)
crop_start = (53, 268)
crop_size = (224, 224)
dark_factor = 0.3

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", required=True, help="path to trained model model")
ap.add_argument("-d", "--dataset", required=True, help="path to test images")
ap.add_argument("-e", "--errors", required=False, help="path to error log file")
ap.add_argument("-r", "--report", required=False, help="path to report log file")
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
#random.shuffle(imagePaths)
print("[INFO] loaded %d images." % (len(imagePaths)))

errors = None
if args['errors']:
    errors = open(args['errors'], "a")
    errors_count = 0

report = None
if args['report']:
    report = open(args['report'], "a")
    report_count = 0

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
    if people > nothing:
        label = "People"
        proba = people
        color = (0, 0, 255)
    else:
        label = "No people"
        proba = nothing
        color = (255, 0, 0)
    label = "{}: {:.2f}%".format(label, proba * 100)
    log_message = "%s - %s" % (imagePath, label)
    print("[%d/%d] %s" % (index, total, log_message))
    if report:
        report.write(log_message + "\n")

    ## display only every 2nd image
    #if index % 2 == 0:
    #    continue

    # darken the ignored image part
    output = (orig * dark_factor).astype(numpy.uint8)
    output[crop_area] = orig[crop_area]

    # put the label
    cv2.putText(output, label, (10, 25),  cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

    # show the output image
    cv2.imshow("Output", output)
    key = cv2.waitKey(1)
    try:
        key = chr(key)
        if key in [ 'q', 'Q' ]:
            break
        if key in [ 'n', 'N' ]:
            if errors:
                errors.write(log_message+"\n")
                errors_count += 1
            print('MISS: %s' % imagePath)
    except:
        pass

if errors:
    print("Added %d misidentified images to %s" % (errors_count, args['errors']))