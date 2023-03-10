from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
import numpy as np
import argparse
import imutils
import time
import cv2
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setup(23,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
red=2
green=3
blue=4
GPIO.setup(red,GPIO.OUT)
GPIO.setup(green,GPIO.OUT)
GPIO.setup(blue,GPIO.OUT)
global r
global g
global b
r=GPIO.PWM(red,100)
g=GPIO.PWM(green,100)
b=GPIO.PWM(blue,100)
def RGB(x,y,z):
    r.start(x)
    g.start(y)
    b.start(z)
RGB(0,0,0)
def detect_and_predict_mask(frame, faceNet, maskNet):
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300),(104.0, 177.0, 123.0))
    faceNet.setInput(blob)
    detections = faceNet.forward()
    faces = []
    locs = []
    preds = []
    for i in range(0, detections.shape[2]):
        confidence = detections[0,0, i,2]
        if confidence > args["confidence"]:
            box = detections[0,0, i,3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")
             (startX, startY) = (max(0, startX), max(0, startY))
             (endX, endY) = (min(w-1, endX), min(h-1, endY))
             face = frame[startY:endY, startX:endX]
             face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
             face = cv2.resize(face, (224, 224))
             face = img_to_array(face)
             face = preprocess_input(face)
             faces.append(face)
             locs.append((startX, startY, endX, endY))
        if len(faces) > 0:
            faces = np.array(faces, dtype="float32")
            preds = maskNet.predict(faces, batch_size=32)
        return (locs, preds)
ap = argparse.ArgumentParser()
ap.add_argument("-f", "--face", type=str,
    default="face_detector",
    help="path to face detector model directory")
ap.add_argument("-m", "--model", type=str,
    default="mask_detector.model",
    help="path to trained face mask detector model")
ap.add_argument("-c", "--confidence", type=float, default=0.5,
    help="minimum probability to filter weak detections")
args = vars(ap.parse_args())

print("[INFO] loading face detector model...")
prototxtPath = os.path.sep.join([args["face"], "deploy.prototxt"])
weightsPath = os.path.sep.join([args["face"],
    "res10_300x300_ssd_iter_140000.caffemodel"])
faceNet = cv2.dnn.readNet(prototxtPath, weightsPath)
print("[INFO] loading face mask detector model...")
maskNet = load_model(args["model"])
while True:
    while GPIO.input(23):
        RGB(100,0,0)
        vs = VideoStream(src=0).start()
        time.sleep(2.0)
        while True:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            (locs, preds) = detect_and_predict_mask(frame, faceNet, maskNet)
            for (box, pred) in zip(locs, preds):
                (mask, withoutMask) = pred
                if mask>withoutMask:
                    print("yes")
                    RGB(0,100,0)
                else:
                    print("non")
                    RGB(100,0,0)
            if GPIO.input(23)==0:
                vs.stop()
                break
RGB(0,0,0)
print("There is nothing")