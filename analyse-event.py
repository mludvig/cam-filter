#!/usr/bin/env python

from __future__ import print_function

# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
from imutils import paths
from datetime import datetime
import numpy as np
import argparse
import imutils
import numpy
import sys
import os
import cv2
from cam_config import cam_config
# HTTP API Server
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

# construct the argument parse and parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model", required = True, help = "Path to trained model")
group = parser.add_mutually_exclusive_group(required = True)
group.add_argument("-d", "--dataset", help = "Path to tested images")
group.add_argument("-p", "--port", type=int, help = "Run API server on this port")

parser.add_argument("-n", "--avg-num", type = int, default = 20, help = "moving average sample length, default = %(default)s")
parser.add_argument("-r", "--report", required = False, help = "Path to report log file")
parser.add_argument("-s", "--save", required = False, help = "Path to directory for storing processed images")
parser.add_argument("-D", "--display", action = "store_true", help = "Display processed images, default=%(default)s")
parser.add_argument("-t", "--threshold", type=float, default = 0.20, required = False, help = "Probability threshold, default=$(default)s")
parser.add_argument("-w", "--wait", action = "store_const", const = 0, default = 1, required = False, help = "Wait for key after displaying each frame")
args = parser.parse_args()

# Prepare crop area
crop_area = numpy.index_exp[
    cam_config.crop_start[0]:cam_config.crop_start[0]+cam_config.crop_size[0],
    cam_config.crop_start[1]:cam_config.crop_start[1]+cam_config.crop_size[1]
]

class APIHandler(BaseHTTPRequestHandler):
    def _send_headers(self, code, content_type = "application/json"):
        self.send_response(code)
        self.send_header('Content-type', content_type)
        self.end_headers()

    def do_GET(self):

        url = urlparse(self.path)
        qs = url.query and parse_qs(url.query) or {}
        if 'event_id' in qs:
            pass
        elif 'dataset' in qs:
            report = process_dataset(qs['dataset'][0])
        else:
            report = { "error": "Either \"event_id\" or \"dataset\" must be sent" }
        if "error" in report:
            self._send_headers(400)
        else:
            self._send_headers(200)
        report_json = json.dumps(report, indent=2)
        self.wfile.write(bytes(report_json, encoding="ascii"))

def run_http_server(port):
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print("[INFO] Running HTTP server on port %d" % port)
    httpd.serve_forever()

def process_dataset(dataset):
    # find the image paths
    print("[INFO] loading images from %s" % dataset)
    t1 = datetime.now()
    imagePaths = sorted(list(paths.list_images(dataset, contains="capture")))
    t2 = datetime.now()
    print("[INFO] loaded %d images in %s" % (len(imagePaths), (t2-t1)))

    report = { "results_fields": [ "result", "p_cur", "p_avg", "img_path" ], "results": [] }

    index = 0
    total = len(imagePaths)
    res_list = []
    avg_list = []
    moving_avg = lambda arr, num: sum(arr[-num:])/len(arr[-num:])

    t1 = datetime.now()
    for imagePath in imagePaths:
        index += 1
        # load the image
        orig = cv2.imread(imagePath)

        # pre-process the image for classification
        image = orig[crop_area]
        image = cv2.resize(image, cam_config.net_size)
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)

        # classify the input image
        (nothing, people) = model.predict(image)[0]
        res_list.append(people)
        avg_list.append(moving_avg(res_list, args.avg_num))

        # build the label
        Pcur = res_list[-1]
        Pcur_str = "%0.2f" % (Pcur * 100)
        if Pcur > args.threshold:
            label = "People %s%%" % Pcur_str
            color = (0, 0, 255)
        else:
            label = "No-people %s%%" % Pcur_str
            color = (255, 0, 0)

        log_label = "unknown"
        if args.save or args.display:
            # darken the ignored image part
            output = (orig * cam_config.dark_factor).astype(numpy.uint8)
            output[crop_area] = orig[crop_area]

            # put the label
            cv2.putText(output, label, (10, 25),  cv2.FONT_HERSHEY_DUPLEX, 0.7, color, 2)

            if args.save:
                dst_path = args.save.rstrip('/') + '/' + os.path.basename(imagePath)
                cv2.imwrite(dst_path, output)

            if args.display:
                # show the output image
                cv2.imshow("Output", output)
                key_raw = cv2.waitKey(args.wait)
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
                except:
                    pass

        # Simple progress indicator
        if (index % int(total/50)) == 0:
            print(".", end="")
            sys.stdout.flush()
        if index == total:
            print("done")

        # Convert from numpy.float32/64 to python native float
        report['results'].append((log_label, float(res_list[-1]), float(avg_list[-1]), imagePath))

    t2 = datetime.now()
    td = (t2-t1).total_seconds()/float(index)
    print("[INFO] processed %d images in %s (%0.4fs per image)" % (index, (t2-t1), td))

    avg_list_max = np.array(avg_list).max()
    result = avg_list_max <= args.threshold and "nothing" or "people"
    report['verdict'] = { "result": result, "p_avg": float(avg_list_max) }

    return report

if __name__ == "__main__":
    # load the trained convolutional neural network
    print("[INFO] loading model...")
    t1 = datetime.now()
    model = load_model(args.model)
    t2 = datetime.now()
    print("[INFO] model loaded in %s" % (t2-t1))

    if args.port:
        run_http_server(args.port)

    else:
        report = process_dataset(args.dataset)
        if args.report:
            with open(args.report, "a") as report_file:
                for result in report['results']:
                    print("%s:%0.4f:%0.4f:%s" % result, file = report_file)
                print("%(result)s:%(p_avg)0.4f::verdict" % report['verdict'], file=report_file)
