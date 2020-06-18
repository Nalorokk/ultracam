import cv2
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import telegram
import tg
from tg import bot
import os
import os.path
import datetime
import numpy as np
import time
import argparse
import shared
from pprint import pprint

classes = None
allowed = ['car', 'bicycle', 'dog', 'motorbike', 'umbrella', 'boat', 'pottedplant', 'fire hydrant', 'train', 'bus', 'bowl', 'cup', 'frisbee']

with open(shared.args.classes, 'r') as f:
    classes = [line.strip() for line in f.readlines()]
COLORS = np.random.uniform(0, 255, size=(len(classes), 3))

notified = []

def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def get_output_layers(net):
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    return output_layers

def save_bounded_image(image, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(classes[class_id])
    dirname = os.path.join(shared.args.outputdir, label, datetime.datetime.now().strftime('%Y-%m-%d'))
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    
    filename = label + '_' + datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f') + '_conf' + "{:.2f}".format(confidence) + '.jpg'
    shared.logger.debug ('Saving bounding box:' + filename)
    roi = image[y:y_plus_h, x:x_plus_w]
    if roi.any():
        if str2bool(shared.args.invertcolor) == False:
            roi = cv2.cvtColor(roi, cv2.COLOR_RGB2BGR)
        cv2.imwrite(os.path.join(dirname, filename), roi)  

def draw_prediction(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
    label = str(classes[class_id])
    color = COLORS[class_id]

    cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 3)
    cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 3)


def perform_alarm(name, image, alarm, silent):
    shared.logger.debug('ALARM!')
    directory = os.path.join('alarm', name, datetime.datetime.now().strftime('%Y-%m-%d'));
    path = os.path.join(directory, datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S_%f')+'.jpg')
    
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    shared.logger.debug('writing to path: '+path)
    cv2.imwrite(path, image)


    caption = '\n'.join(alarm)
    
    if(silent):
        caption = 'type: notification\n' + caption
    else:
        caption = 'type: alarm\n' + caption

    msgId = shared.config['tg_chat']
    try:
    	bot.send_photo(chat_id=msgId, photo=open(path, 'rb'), caption = caption, disable_notification = silent)

    except:
    	shared.logger.debug('Telegram error happened')


def get_image_difference(image_1, image_2):
        first_image_hist = cv2.calcHist([image_1], [0], None, [256], [0, 256])
        second_image_hist = cv2.calcHist([image_2], [0], None, [256], [0, 256])

        img_hist_diff = cv2.compareHist(first_image_hist, second_image_hist, cv2.HISTCMP_BHATTACHARYYA)
        img_template_probability_match = cv2.matchTemplate(first_image_hist, second_image_hist, cv2.TM_CCOEFF_NORMED)[0][0]
        img_template_diff = 1 - img_template_probability_match

        # taking only 10% of histogram diff, since it's less accurate than template method
        commutative_image_diff = (img_hist_diff / 10) + img_template_diff
        return commutative_image_diff

def detect(stream):
    name = stream['label']
    name2 = name+'_processed'
    image = shared.framebuffer[name]

    if name2 in shared.framebuffer:
        commutative_image_diff = get_image_difference(shared.framebuffer[name], shared.framebuffer[name2])
        pprint(commutative_image_diff)
        shared.increase_counter("total_diff", commutative_image_diff)
        shared.increase_counter("total_processed")
        shared.add_framestat(name, commutative_image_diff)

        if(commutative_image_diff < 0.0025):
            shared.increase_counter("total_skip_diff", commutative_image_diff)
            pprint("skipping frame")
            return None

    shared.framebuffer[name2] = image

    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392
    
    net = cv2.dnn.readNet(shared.args.weights, shared.args.config)
    
    blob = cv2.dnn.blobFromImage(image, scale, (416,416), (0,0,0), True, crop=False)
    
    net.setInput(blob)
    
    outs = net.forward(get_output_layers(net))
    
    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = 0.5
    nms_threshold = 0.4
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                center_x = int(detection[0] * Width)
                center_y = int(detection[1] * Height)
                w = int(detection[2] * Width)
                h = int(detection[3] * Height)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([x, y, w, h])
    
    
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
    
    alarm = []
    silent = True
    polygon = None

    if('detect_in_polygon' in stream):
        polygon = Polygon(stream['detect_in_polygon'])

    orgImage = image.copy()
    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]
        save_bounded_image(orgImage, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))
        draw_prediction(image, class_ids[i], confidences[i], round(x), round(y), round(x+w), round(y+h))

        point_loc = round(x + w/2), round(y + h/2)
        point = Point(*point_loc)

        alarmObjectName = str(classes[class_ids[i]])
        if(alarmObjectName not in allowed and checkAlarm(alarmObjectName, point_loc, confidences[i])):
            if(polygon is None):
                alarm.append('{}: {:.2%}'.format(alarmObjectName, confidences[i]))
                silent = False
            else:
                alarm.append('{}: {:.2%}'.format(alarmObjectName, confidences[i]))
                if(polygon.contains(point)):
                    cv2.circle(image, point_loc, 5, (0, 0, 255), -1)
                    silent = False
                else:
                    cv2.circle(image, point_loc, 5, (0, 255, 0), -1)

            
        else:
            shared.logger.debug('Found '+alarmObjectName+' ignoring')

    if str2bool(shared.args.invertcolor) == True:
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if len(alarm) > 0:
        perform_alarm(name, image, alarm, silent)
    return image

def checkAlarm(name, point, confidence):
    global notified
    if(confidence > 0.9):
        shared.logger.debug('Always allow high confidence')
        return True
    else:
        for alarm in notified:
            if(alarm['name'] == name and abs(alarm['point'][0] - point[0]) + abs(alarm['point'][1] - point[1]) < 15 and confidence - alarm['confidence'] < 10 and time.time() - alarm['time'] < 60 * 30):
                shared.logger.debug('Treating incoming alarm '+name+' '+str(confidence)+' as repeat of previous')
                return False

        notified.append({'name':name, 'point':point, 'confidence':confidence, 'time': time.time()})
        pprint(notified)
        return True




def processFrame():
    while True:
        for stream in shared.config['streams']:
            if(stream['label'] in shared.framebuffer):
                shared.logger.debug('Processing frame named: '+stream['label'])
                begin = time.time()

                framed = detect(stream)
                if framed is not None:
                    shared.framebuffer[stream['label'] + '_framed'] = framed

                    took = time.time() - begin

                    shared.increase_counter('images_processed')
                    shared.increase_counter('images_time', took)
                    shared.logger.debug('detection tooks: '+str(took)+' seconds')
                else:
                    took = time.time() - begin
                    shared.increase_counter('images_skipped')
                    shared.increase_counter('skipped_time', took)
            
        time.sleep(0.5)
