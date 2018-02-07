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
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", required=True, help="path to trained model model")
ap.add_argument("-d", "--dataset", required=True, help="path to test images")
ap.add_argument("-e", "--errors", required=False, help="path to error log file")
ap.add_argument("-r", "--report", required=False, help="path to report log file")
args = vars(ap.parse_args())

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
    orig = orig[53:53+224, 268:268+224]       # crop to 224x224 starting from 53:268 (h:w)
    #cv2.imshow("Image", image)
    #key = cv2.waitKey(0)
    image = cv2.resize(orig, (28, 28))         # resize
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

    # draw the label on the image
    #output = imutils.resize(orig, width=400)
    output = orig
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