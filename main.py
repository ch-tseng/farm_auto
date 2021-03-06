#!/home/pi/envs/plants/bin/python
# -*- coding: utf-8 -*-

import spidev
import RPi.GPIO as GPIO
import sys, time, os
from datetime import datetime
import cv2
import imutils
import numpy as np
from numpy import interp
import matplotlib.pyplot as plot
from PIL import ImageFont, ImageDraw, Image

#-----------------------------------
plotLength = 60
lightTime = (6,18)  #hour
waterTime = (5,18) # hour
waterInterval =  2 * 60 * 60 #seconds
wateringTimeLength = 15  #seconds

pinLight = 14
pinWater = 15
pinSoil = 18

light_time = [6, 18]
water_time = [8, 18]
th_light = 95
th_water = 16
interval_watering = 15  #minutes 
watering_powron_time = 10   #seconds

img_rotate = 0
img_flip_v = True
img_flip_h = True
img_display_resize_w = 500  #resize for webcam

#------------------------------------

GPIO.setmode(GPIO.BCM)
GPIO.setup(pinLight, GPIO.OUT)
GPIO.setup(pinWater, GPIO.OUT)
GPIO.setup(pinSoil, GPIO.IN)

GPIO.output(pinWater, GPIO.HIGH)
GPIO.output(pinLight, GPIO.HIGH)

spi = spidev.SpiDev()
spi.open(0,0)

figure = plot.figure(num=None, figsize=(15, 4), dpi=50, facecolor='w', edgecolor='k')
ax_l = figure.add_subplot(1,2,1)
ax_w = figure.add_subplot(1,2,2)

lList = []
wList = []
timeList_l = []
timeList_w = []

#top-left , bottom-right, color
addY =200
lastWatering = 0  #last watering time
plant_box = [[(15,40+addY),(165,261+addY),(254,166,12),"雪荔", "wav/plant_1.wav"],\
            [(118,17+addY),(474,255+addY),(12,143,254), "竹柏", "wav/plant_2.wav"],\
            [(60, 210+addY),(172,318+addY),(5,5,255),"嫣紅蔓", "wav/plant_5.wav"],\
            [(130, 232+addY),(338,380+addY),(40,255,5),"長春藤", "wav/plant_4.wav"],\
            [(267, 182+addY),(448,325+addY),(252,7,140),"紅網紋", "wav/plant_3.wav"] ]

cv2.namedWindow("Plant Image", cv2.WND_PROP_FULLSCREEN)        # Create a named window
cv2.setWindowProperty("Plant Image", cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)

def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    vdata = interp(data, [0, 1023], [0, 100])

    return vdata


def speak(wavfile):
    os.system('/usr/bin/aplay ' + wavfile)

def read_soil():
    #GPIO.input(pinSoil)
    value = analogInput(0)
    value = 100 - value
    print("SOIL:", value)

    return value

def read_light():
    value = analogInput(1)
    print("Light:", value)

    return value

def draw_plant_box(img):
    y_txt = 105 + addY
    for i in range(0,len(plant_box)):
        cv2.rectangle(img,plant_box[i][0],plant_box[i][1],plant_box[i][2],3)
        #time.sleep(1)
        cv2.waitKey(1000)
        img = printText(plant_box[i][3], img, color=(plant_box[i][2][0],plant_box[i][2][1],plant_box[i][2][2],0), size=0.8, pos=(550,y_txt), type="Chinese")
        #time.sleep(1.5)
        #cv2.waitKey(1500)
        y_txt = y_txt + 30

        cv2.imshow("Plant Image", img)
        cv2.waitKey(1)
        cv2.waitKey(1)
        speak(plant_box[i][4])
    return img

def light_control(img, nValue):
    y_txt = 105 + addY
    
    now = datetime.now()
    hourNow = int(now.strftime("%H"))
    startHour = light_time[0]
    endHour = light_time[1]
    
    img = printText("植物的照光時間設定：", img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
    y_txt += 30
    img = printText(str(light_time[0]) + "點 ~ " + str(light_time[1])+"點", img, color=(4,197,252,0), size=0.7, pos=(600,y_txt), type="Chinese")
    y_txt += 60
    img = printText("目前光照度為"+str(int(nValue)), img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
    y_txt += 30

    if(hourNow>=startHour and hourNow<=endHour):
        if(nValue>th_light):
            img = printText("高於設定值"+str(th_light), img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
            y_txt += 50
            img = printText("光照足夠!", img, color=(102,102,254,0), size=0.7, pos=(600,y_txt), type="Chinese")
            y_txt += 30
            img = printText("不需開啟LED植物燈", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
            speakFile = "wav/light_1.wav"
        else:
            img = printText("未達到設定值"+str(th_light), img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
            y_txt += 50
            img = printText("光照不足!", img, color=(102,102,254,0), size=0.7, pos=(600,y_txt), type="Chinese")
            y_txt += 30
            img = printText("已開啟LED植物燈補光", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
            GPIO.output(pinLight, GPIO.LOW)
            speakFile = "wav/light_2.wav"

    else:
        y_txt += 50
        img = printText("非光照時間", img, color=(0,255,0,0), size=0.7, pos=(550,y_txt), type="Chinese")
        speakFile = "wav/light_3.wav"

    cv2.imshow("Plant Image", img)
    cv2.waitKey(1)
    cv2.waitKey(1)
    speak(speakFile)
    cv2.waitKey(3000)

    return img

def water_control(img, nValue):
    global lastWatering

    y_txt = 105 + addY
    now = datetime.now()
    hourNow = int(now.strftime("%H"))
    startHour = water_time[0]
    endHour = water_time[1]

    img = printText("植物的澆水時間設定：", img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
    y_txt += 30
    img = printText(str(water_time[0]) + "點 ~ " + str(water_time[1])+"點", img, color=(4,197,252,0), size=0.7, pos=(600,y_txt), type="Chinese")
    y_txt += 60
    img = printText("目前土壤溼度為"+str(int(nValue)), img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
    y_txt += 30

    ynWater = False

    if(hourNow>=startHour and hourNow<=endHour):
        if(nValue>th_water):
            img = printText("高於設定值"+str(th_water), img, color=(255,255,255,0), size=0.7, pos=(600,y_txt), type="Chinese")
            y_txt += 60
            img = printText("不需要澆水!", img, color=(102,102,254,0), size=0.7, pos=(600,y_txt), type="Chinese")
            speakFile = "wav/water_1.wav"
        else:
            img = printText("低於設定值"+str(th_water), img, color=(255,255,255,0), size=0.7, pos=(530,y_txt), type="Chinese")
            y_txt += 60
            water_idled = time.time()-lastWatering

            if(water_idled>(interval_watering*60)):
                img = printText("需要澆水!", img, color=(102,102,254,0), size=0.7, pos=(600,y_txt), type="Chinese")
                y_txt += 30
                img = printText("已啟動汲水幫浦", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
                speakFile = "wav/water_2.wav"
                ynWater = True
                lastWatering = time.time()

            else:
                img = printText("需要澆水但尚未超過澆水", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
                y_txt += 30
                img = printText("間隔時間"+str(interval_watering)+"分鐘", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
                y_txt += 30
                img = printText("須再等待"+str(int(interval_watering*60 - water_idled))+"秒鐘", img, color=(102,102,254,0), size=0.7, pos=(550,y_txt), type="Chinese")
                speakFile = "wav/water_3.wav"

    else:
        y_txt += 50
        img = printText("非澆水時間", img, color=(0,0,255,0), size=0.7, pos=(550,y_txt), type="Chinese")
        speakFile = "wav/water_4.wav"

    cv2.imshow("Plant Image", img)
    cv2.waitKey(1)
    cv2.waitKey(1)
    cv2.waitKey(10)
    speak(speakFile)
    if(ynWater is True):
        watering()

    return img

def printText(txt, bg, color=(0,255,0,0), size=0.7, pos=(0,0), type="Chinese"):
    (b,g,r,a) = color

    if(type=="English"):
        ## Use cv2.FONT_HERSHEY_XXX to write English.
        cv2.putText(bg,  txt, pos, cv2.FONT_HERSHEY_SIMPLEX, size,  (b,g,r), 2, cv2.LINE_AA)

    else:
        ## Use simsum.ttf to write Chinese.
        fontpath = "wt009.ttf"
        #print("TEST", txt)
        font = ImageFont.truetype(fontpath, int(size*10*3.2))
        img_pil = Image.fromarray(bg)
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos,  txt, font = font, fill = (b, g, r, a))
        bg = np.array(img_pil)

    return bg

def inputData(arrayName, data, length):
    if(len(arrayName)>length):
        arrayName.pop(0)

    arrayName.append(data)

    return arrayName

def watering():
    print("start watering...")
    startWater = time.time()

    while time.time()-startWater<watering_powron_time:
        GPIO.output(pinWater, GPIO.LOW)

    GPIO.output(pinWater, GPIO.HIGH)

def plotLine(img_bg, vLight, vWater):
    global lList, wList, timeList_l, timeList_w

    lList = inputData(lList, vLight, plotLength)
    timeList_l = inputData(timeList_l, dataTime, plotLength)

    wList = inputData(wList, vWater, plotLength)
    timeList_w = inputData(timeList_w, dataTime, plotLength)

    # draw a cardinal sine plot
    x = np.array (timeList_l )
    y = np.array (lList)
    ax_l.cla()
    ax_l.set_title("Lightness (degree)")
    ax_l.set_ylim(0, 100)
    ax_l.axes.get_xaxis().set_visible(False)
    ax_l.plot ( x, y ,'yo-')

    x = np.array (timeList_w )
    y = np.array (wList)
    ax_w.cla()
    ax_w.set_title("Water (degree)")
    ax_w.set_ylim(0, 100)
    ax_w.axes.get_xaxis().set_visible(False)
    ax_w.plot ( x, y , 'bo-')


    figure.canvas.draw()
    # convert canvas to image
    img = np.fromstring(figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    img  = img.reshape(figure.canvas.get_width_height()[::-1] + (3,))
    # img is rgb, convert to opencv's default bgr
    img = cv2.cvtColor(img,cv2.COLOR_RGB2BGR)
    print("img:", img.shape[0], img.shape[1])
    print("bg", img_bg.shape[0]-220, img_bg.shape[1])
    #matplotlib.pyplot.show()
    img_bg[ 0:img.shape[0], 10:10+img.shape[1]] = img

    return img_bg

def contrast_stretch(im):
    """
    Performs a simple contrast stretch of the given image, from 5-95%.
    """
    in_min = np.percentile(im, 5)
    in_max = np.percentile(im, 95)

    out_min = 0.0
    out_max = 255.0

    out = im - in_min
    out *= ((out_min - out_max) / (in_min - in_max))
    out += in_min

    return out


def ndvi(image):
    # use Standard NDVI method, smaller for larger area
    thRED1 = 150
    thYELLOW1 = 60
    thGREEN1 = 0

    #image = cv2.bitwise_and(image, image, mask=cv2.imread("9_or_joined.png"))
    r, g, b = cv2.split(image)
    divisor = (r.astype(float) + b.astype(float))
    divisor[divisor == 0] = 0.01  # Make sure we don't divide by zero!

    ndvi = (b.astype(float) - r) / divisor

    #Paint the NDVI image
    ndvi2 = contrast_stretch(ndvi)
    ndvi2 = ndvi2.astype(np.uint8)

    redNDVI = cv2.inRange(ndvi2, thRED1, 255)
    yellowNDVI = cv2.inRange(ndvi2, thYELLOW1, thRED1)
    greenNDVI = cv2.inRange(ndvi2, thGREEN1, thYELLOW1)
    merged = cv2.merge([yellowNDVI, greenNDVI, redNDVI])

    #text = '[Max]: {m} '.format(m=round(ndvi.max(),1))
    #text = text + '[Mean]: {m} '.format(m=round(ndvi.mean(),1))
    #text = text + '[Median]: {m} '.format(m=round(np.median(ndvi),1))
    #text = text + '[Min]: {m}'.format(m=round(ndvi.min(),1))
    return merged

if __name__ == "__main__":

    #bg = cv2.imread("bg_main.png")

    INPUT = cv2.VideoCapture(0)
    width = int(INPUT.get(cv2.CAP_PROP_FRAME_WIDTH))   # float
    height = int(INPUT.get(cv2.CAP_PROP_FRAME_HEIGHT)) # float
    hasFrame = True

    i = 0
    while hasFrame:
        now = datetime.now()
        dataTime = now.strftime("%H:%M:%S")

        hasFrame, frame = INPUT.read()
        if(img_rotate>0):
            frame = imutils.rotate_bound(frame, img_rotate)
        if(img_flip_h is True):
            frame = cv2.flip(frame, 1 , dst=None)
        if(img_flip_v is True):
            frame = cv2.flip(frame, 0 , dst=None)

        if(i % 4 == 3):
            bg = cv2.imread("bg_main_detect.png")
        elif(i % 4 == 0):
            bg = cv2.imread("bg_main_light.png")
        elif(i % 4 == 1):
            bg = cv2.imread("bg_main_water.png")
        elif(i % 4 == 2):
            bg = cv2.imread("bg_main_ndvi.png")


        now_light = read_light()
        now_water = read_soil()
        bg = plotLine(bg, now_light, now_water)
        frame_display = imutils.resize(frame, width=img_display_resize_w)
        #bg[12:12+frame_display.shape[0], 12:12+frame_display.shape[1]] = frame_display
        if(i % 4 == 2):
            frame_display = ndvi(frame_display)

        bg[bg.shape[0]-frame_display.shape[0]-15:bg.shape[0]-15, 12:12+frame_display.shape[1]] = frame_display

        if(i % 4 == 3):
            final_display = draw_plant_box(bg)
        elif(i % 4 == 0):
            final_display = light_control(bg, now_light)
        elif(i % 4 == 1):
            final_display = water_control(bg, now_water)
        elif( i % 4 == 2):
            final_display = bg

        cv2.imshow("Plant Image", final_display)
        #cv2.imwrite("test.jpg", bg)
        cv2.waitKey(1)
        cv2.waitKey(10)
        if(i % 4 == 2):
            speak("wav/ndvi_1.wav")
            cv2.waitKey(1500)
        i += 1
