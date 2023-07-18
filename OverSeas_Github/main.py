import os
import cv2
import time
import json
import socketio
import pyqrcode
import threading
import numpy as np
from yolo_segmentation import YOLOSegmentation

url = "http://localhost/"
device_id = '111'
pyqrcode.create(url).png("qrcode.png", scale=10)
qr = cv2.imread("qrcode.png")
qr = cv2.resize(qr, (200, 200))

filter_id = '0'

def ws_download(url, ad_id):
    print("Downloading")
    print('url: ' + url)
    print('ad_id: ' + ad_id)

def ws_delete(ad_id):
    print("Deleting", ad_id)

def ws_upload():
    print("Uploading")

def ws_connect():
    global sio
    sio = socketio.Client()
    while True:
        try:
            # sio.connect('http://ws.marwiztech.com')
            sio.connect('http://localhost:3000')
            break
        except:
            print("Connection failed")
            time.sleep(5)

threading.Thread(target=ws_connect).start()

if sio.connected:
    print("Connected")
    sio.emit('message', device_id)

@sio.event
def connect():
    print('Connected to server')
    sio.emit('message', device_id)

@sio.event
def message(data):
    global filter_id
    message = json.loads(data)
    print(message)

    if message['action'] == 'Download Media':
        ws_download(message['data']['mediaurl'], message['data']['ad_id'])
    elif message['action'] == 'Delete Media':
        ws_delete(message['data']['ad_id'])
    elif message['action'] == 'Upload images':
        ws_upload()
    elif message['action'] == 'Take picture':
        take_picture()
    elif message['action'] == 'Update filter':
        filter_id = message['data']['filterId']
        print("Filter updated to", filter_id)

@sio.event
def disconnect():
    print('Disconnected from server')

@sio.on('imageReceived')
def on_image_received(data):
    print(data['message'])
    print('Image filename:', data['filename'])
    print('Image saved at:', data['imagePath'])

def take_picture():
    global save
    image_name = f"image_{int(time.time())}.jpg"
    print("Taking image")
    cv2.imwrite("Images/"+image_name, save)

    time.sleep(0.2)
    with open(os.path.join('Images/', image_name), 'rb') as file:
        sio.emit('image', {'data': file.read(), 'filename': image_name})

ys = YOLOSegmentation("yolov8m-seg.pt")
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
# default_bg = cv2.imread('bg_3.jpg')

while True:
    check, img = cap.read()
    h,w,_ = img.shape
    # print(img.shape)
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    # img = cv2.imread("C:/Users/LENOVO/Pictures/Camera Roll/WIN_20230717_22_11_16_Pro.jpg")

    try:
        bboxes, classes, segmentations, scores = ys.detect(img)
        for bbox, class_id, seg, score in zip(bboxes, classes, segmentations, scores):
            # print("bbox:", bbox, "class id:", class_id, "seg:", seg, "score:", score)
            (x, y, x2, y2) = bbox
            if class_id == 0:
                # cv2.polylines(img, [seg], True, (0, 0, 255), 4)
                cv2.fillPoly(mask, [seg], 255)

                region = cv2.bitwise_and(img, img, mask=mask)
    except:
        print("Object Not Detected")


    if filter_id == '0':
        default_bg = cv2.imread('bg_3.jpg')
        default_bg = cv2.resize(default_bg, (1080, 1920))

    elif filter_id == '2':
        default_bg = cv2.imread('2.jpg')
        default_bg = cv2.resize(default_bg, (1080, 1920))
        region = cv2.resize(region, (960, 720))
        try:
            default_bg[1000:1720, 0:960] = np.where(region == (0,0,0), default_bg[1000:1720, 0:960], region)
        except:
            print("Object Undetected.")

    elif filter_id == '3':
        default_bg = cv2.imread('3.jpg')
        default_bg = cv2.resize(default_bg, (1080, 1920))
        try:
            default_bg[1440:1920, 220:860] = np.where(region == (0,0,0), default_bg[1440:1920, 220:860], region)
        except:
            print("Object Undetected")

    elif filter_id == '4':
        default_bg = cv2.imread('4.jpg')
        default_bg = cv2.resize(default_bg, (1080, 1920))
        region = cv2.resize(region, (960, 720))
        try:
            default_bg[1100:1820, 60:1020] = np.where(region == (0,0,0), default_bg[1100:1820, 60:1020], region)
        except:
            print("Object Undetected")

    # if filter_id != '0':
    #     try:
    #         default_bg[900:1620, 0:960] = np.where(region == (0,0,0), default_bg[900:1620, 0:960], region)
    #         save = default_bg.copy()
    #     except:
    #         print("Object Undetected.")

    cv2.namedWindow('background', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('background', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("background", default_bg)
    key = cv2.waitKey(1)
    if key == 27:
        os._exit(0)