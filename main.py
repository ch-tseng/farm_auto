#!/home/pi/envs/plants/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import sys, time, os
from datetime import datetime
import cv2
import imutils
import numpy as np
import matplotlib.pyplot as plot
from PIL import ImageFont, ImageDraw, Image

#-----------------------------------
plotLength = 30
thLight = 950
thWater = 20
lightTime = (6,18)  #hour
waterTime = (5,18) # hour
waterInterval =  2 * 60 * 60 #seconds
wateringTimeLength = 15  #seconds

pinLight = 14
pinWater = 15
pinSoil = 18

img_rotate = 0
img_flip_v = True
img_flip_h = True
img_display_resize_w = 500

#------------------------------------

GPIO.setmode(GPIO.BCM)
GPIO.setup(pinLight, GPIO.OUT)
GPIO.setup(pinWater, GPIO.OUT)
GPIO.setup(pinSoil, GPIO.IN)

#top-left , bottom-right, color
plant_box = [[(15,40),(165,261),(254,166,12),"雪荔"], [(118,17),(474,255),(12,143,254), "竹柏"],\
        [(60, 210),(172,318),(5,5,255),"紅網紋"], [(130, 232),(338,380),(40,255,5),"長春藤"],\
        [(267, 182),(448,325),(5,5,255),"嫣紅蔓"] ]

def read_soil():
    #GPIO.input(pinSoil)
    return 0.4

def read_light():
    return 755

def draw_plant_box(img):
    y_txt = 105
    for i in range(0,len(plant_box)):
        cv2.rectangle(img,plant_box[i][0],plant_box[i][1],plant_box[i][2],3)
        img = printText(plant_box[i][3], img, color=(plant_box[i][2][0],plant_box[i][2][1],plant_box[i][2][2],0), size=0.8, pos=(550,y_txt), type="Chinese")
        y_txt = y_txt + 30

    return img

def printText(txt, bg, color=(0,255,0,0), size=0.7, pos=(0,0), type="Chinese"):
    (b,g,r,a) = color

    if(type=="English"):
        ## Use cv2.FONT_HERSHEY_XXX to write English.
        cv2.putText(bg,  txt, pos, cv2.FONT_HERSHEY_SIMPLEX, size,  (b,g,r), 2, cv2.LINE_AA)

    else:
        ## Use simsum.ttf to write Chinese.
        fontpath = "wt009.ttf"
        print("TEST", txt)
        font = ImageFont.truetype(fontpath, int(size*10*3))
        img_pil = Image.fromarray(bg)
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos,  txt, font = font, fill = (b, g, r, a))
        bg = np.array(img_pil)

    return bg


if __name__ == "__main__":

    bg = cv2.imread("bg_main.png")

    INPUT = cv2.VideoCapture(0)
    width = int(INPUT.get(cv2.CAP_PROP_FRAME_WIDTH))   # float
    height = int(INPUT.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float
    hasFrame = True

    while hasFrame:
        hasFrame, frame = INPUT.read()
        if(img_rotate>0):
            frame = imutils.rotate_bound(frame, img_rotate)
        if(img_flip_h is True):
            frame = cv2.flip(frame, 1 , dst=None)
        if(img_flip_v is True):
            frame = cv2.flip(frame, 0 , dst=None)


        frame_display = imutils.resize(frame, width=img_display_resize_w)
        bg[12:12+frame_display.shape[0], 12:12+frame_display.shape[1]] = frame_display
        cv2.imwrite("test.jpg", bg)
        bg = draw_plant_box(bg)
        cv2.imshow("TEST", bg)
        cv2.waitKey(1)
